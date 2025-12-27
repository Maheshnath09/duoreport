"""
DuoReport - Realtime Collaborative Report Editor
A FastAPI-based application for exactly 2 users to collaborate on reports in real-time.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import redis.asyncio as aioredis
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import requests
import json
import asyncio
import time
import uuid
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional
import re

app = FastAPI(title="DuoReport", description="Realtime Collaborative Report Editor")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Redis connection
redis_client: Optional[aioredis.Redis] = None

# Document template sections
TEMPLATE_SECTIONS = {
    "abstract": "",
    "introduction": "",
    "methodology": "",
    "results": "",
    "conclusion": "",
    "references": ""
}

SECTION_TITLES = {
    "abstract": "Abstract",
    "introduction": "Introduction",
    "methodology": "Methodology",
    "results": "Results",
    "conclusion": "Conclusion",
    "references": "References"
}


class ConnectionManager:
    """Manages WebSocket connections for each room"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[Dict]] = {}
        self.auto_save_tasks: Dict[str, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str, username: str) -> bool:
        """Connect a user to a room. Returns False if room is full (2 users max)"""
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        
        # Check if room is full (max 2 users)
        if len(self.active_connections[room_id]) >= 2:
            await websocket.send_json({
                "type": "error",
                "message": "Room is full. Only 2 users allowed per room."
            })
            await websocket.close()
            return False
        
        # Add connection
        connection_info = {
            "websocket": websocket,
            "username": username,
            "connected_at": time.time()
        }
        self.active_connections[room_id].append(connection_info)
        
        # Start auto-save task if not already running
        if room_id not in self.auto_save_tasks:
            self.auto_save_tasks[room_id] = asyncio.create_task(
                self.auto_save_loop(room_id)
            )
        
        return True
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        """Disconnect a user from a room"""
        if room_id in self.active_connections:
            self.active_connections[room_id] = [
                conn for conn in self.active_connections[room_id]
                if conn["websocket"] != websocket
            ]
            
            # Clean up empty rooms
            if len(self.active_connections[room_id]) == 0:
                del self.active_connections[room_id]
                
                # Cancel auto-save task
                if room_id in self.auto_save_tasks:
                    self.auto_save_tasks[room_id].cancel()
                    del self.auto_save_tasks[room_id]
    
    async def broadcast(self, room_id: str, message: dict, exclude: Optional[WebSocket] = None):
        """Broadcast message to all users in a room except the sender"""
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                if connection["websocket"] != exclude:
                    try:
                        await connection["websocket"].send_json(message)
                    except Exception as e:
                        print(f"Error broadcasting to user: {e}")
    
    async def auto_save_loop(self, room_id: str):
        """Auto-save document every 5 seconds"""
        try:
            while True:
                await asyncio.sleep(5)
                # Update last_active timestamp
                if redis_client:
                    doc_key = f"report:{room_id}"
                    doc_data = await redis_client.get(doc_key)
                    if doc_data:
                        doc = json.loads(doc_data)
                        doc["last_active"] = time.time()
                        await redis_client.setex(
                            doc_key,
                            3600,  # 1 hour expiry
                            json.dumps(doc)
                        )
        except asyncio.CancelledError:
            pass
    
    def get_users(self, room_id: str) -> List[str]:
        """Get list of usernames in a room"""
        if room_id in self.active_connections:
            return [conn["username"] for conn in self.active_connections[room_id]]
        return []


manager = ConnectionManager()


@app.on_event("startup")
async def startup_event():
    """Initialize Redis connection on startup"""
    global redis_client
    try:
        redis_client = await aioredis.from_url(
            "redis://localhost:6379",
            encoding="utf-8",
            decode_responses=True
        )
        print("✓ Connected to Redis")
    except Exception as e:
        print(f"✗ Failed to connect to Redis: {e}")
        print("Please ensure Redis is running on localhost:6379")


@app.on_event("shutdown")
async def shutdown_event():
    """Close Redis connection on shutdown"""
    if redis_client:
        await redis_client.close()


@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main HTML page"""
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/create_room")
async def create_room():
    """Create a new room with a unique ID and initialize document template"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    room_id = str(uuid.uuid4())[:8]  # Short UUID
    
    # Initialize document in Redis
    doc_data = {
        "sections": TEMPLATE_SECTIONS.copy(),
        "cursors": {},
        "last_active": time.time(),
        "created_at": time.time()
    }
    
    await redis_client.setex(
        f"report:{room_id}",
        3600,  # 1 hour expiry
        json.dumps(doc_data)
    )
    
    return {"room_id": room_id}


@app.websocket("/ws/report/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """WebSocket endpoint for realtime collaboration"""
    
    # Accept the WebSocket connection FIRST
    await websocket.accept()
    
    # Wait for username from client
    try:
        init_message = await websocket.receive_json()
        username = init_message.get("username", "Anonymous")
    except:
        await websocket.close()
        return
    
    # Check if room is full (max 2 users)
    if room_id in manager.active_connections and len(manager.active_connections[room_id]) >= 2:
        await websocket.send_json({
            "type": "error",
            "message": "Room is full. Only 2 users allowed per room."
        })
        await websocket.close()
        return
    
    # Add connection to manager
    if room_id not in manager.active_connections:
        manager.active_connections[room_id] = []
    
    connection_info = {
        "websocket": websocket,
        "username": username,
        "connected_at": time.time()
    }
    manager.active_connections[room_id].append(connection_info)
    
    # Start auto-save task if not already running
    if room_id not in manager.auto_save_tasks:
        manager.auto_save_tasks[room_id] = asyncio.create_task(
            manager.auto_save_loop(room_id)
        )
    
    try:
        # Load initial document
        if redis_client:
            doc_key = f"report:{room_id}"
            doc_data = await redis_client.get(doc_key)
            
            if doc_data:
                doc = json.loads(doc_data)
            else:
                # Create new document if doesn't exist
                doc = {
                    "sections": TEMPLATE_SECTIONS.copy(),
                    "cursors": {},
                    "last_active": time.time()
                }
                await redis_client.setex(doc_key, 3600, json.dumps(doc))
            
            # Send initial state to user
            await websocket.send_json({
                "type": "init",
                "document": doc,
                "username": username,
                "users": manager.get_users(room_id)
            })
            
            # Notify other users
            await manager.broadcast(room_id, {
                "type": "user_joined",
                "username": username,
                "users": manager.get_users(room_id)
            }, exclude=websocket)
        
        # Listen for messages
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "edit":
                # Handle document edit
                section = data.get("section")
                delta = data.get("delta")
                content = data.get("content")
                
                if redis_client and section:
                    # Update document in Redis
                    doc_data = await redis_client.get(doc_key)
                    if doc_data:
                        doc = json.loads(doc_data)
                        if content is not None:
                            doc["sections"][section] = content
                        doc["last_active"] = time.time()
                        await redis_client.setex(doc_key, 3600, json.dumps(doc))
                    
                    # Broadcast to other users
                    await manager.broadcast(room_id, {
                        "type": "edit",
                        "section": section,
                        "delta": delta,
                        "content": content,
                        "username": username
                    }, exclude=websocket)
            
            elif message_type == "cursor":
                # Handle cursor position update
                section = data.get("section")
                position = data.get("position")
                
                # Broadcast cursor position
                await manager.broadcast(room_id, {
                    "type": "cursor",
                    "section": section,
                    "position": position,
                    "username": username
                }, exclude=websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast(room_id, {
            "type": "user_left",
            "username": username,
            "users": manager.get_users(room_id)
        })
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, room_id)


@app.get("/export/{room_id}")
async def export_pdf(room_id: str):
    """Export document as PDF"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    # Load document from Redis
    doc_key = f"report:{room_id}"
    doc_data = await redis_client.get(doc_key)
    
    if not doc_data:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = json.loads(doc_data)
    sections = doc.get("sections", {})
    
    # Create PDF
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#1a1a1a',
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor='#2563eb',
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        textColor='#374151',
        spaceAfter=12,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )
    
    # Title page
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("DuoReport", title_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"Room ID: {room_id}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(PageBreak())
    
    # Add sections
    for section_key in ["abstract", "introduction", "methodology", "results", "conclusion", "references"]:
        section_title = SECTION_TITLES.get(section_key, section_key.title())
        section_content = sections.get(section_key, "")
        
        # Add section heading
        story.append(Paragraph(section_title, heading_style))
        
        # Clean HTML and add content
        if section_content:
            # Remove HTML tags for PDF
            clean_content = re.sub('<[^<]+?>', '', section_content)
            clean_content = clean_content.replace('&nbsp;', ' ')
            clean_content = clean_content.strip()
            
            if clean_content:
                story.append(Paragraph(clean_content, body_style))
            else:
                story.append(Paragraph("<i>No content</i>", body_style))
        else:
            story.append(Paragraph("<i>No content</i>", body_style))
        
        story.append(Spacer(1, 0.3*inch))
    
    # Build PDF
    pdf.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{room_id}.pdf"}
    )


@app.post("/summarize/{room_id}/{section}")
async def summarize_section(room_id: str, section: str):
    """Summarize a section using Hugging Face API"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    # Load document from Redis
    doc_key = f"report:{room_id}"
    doc_data = await redis_client.get(doc_key)
    
    if not doc_data:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = json.loads(doc_data)
    sections = doc.get("sections", {})
    section_content = sections.get(section, "")
    
    if not section_content:
        return JSONResponse({"summary": ["No content to summarize"]})
    
    # Clean HTML tags
    clean_content = re.sub('<[^<]+?>', '', section_content)
    clean_content = clean_content.replace('&nbsp;', ' ').strip()
    
    if len(clean_content) < 50:
        return JSONResponse({"summary": ["Content too short to summarize"]})
    
    # Call Hugging Face API
    try:
        API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        
        response = requests.post(
            API_URL,
            headers={"Content-Type": "application/json"},
            json={"inputs": clean_content[:1024]},  # Limit input length
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                summary_text = result[0].get("summary_text", "")
                # Split into bullet points
                sentences = summary_text.split('. ')
                summary_bullets = [s.strip() + '.' for s in sentences if s.strip()]
                return JSONResponse({"summary": summary_bullets})
        
        # Fallback if API fails
        return JSONResponse({"summary": ["Summary generation temporarily unavailable. Please try again."]})
    
    except Exception as e:
        print(f"Summarization error: {e}")
        return JSONResponse({"summary": ["Error generating summary. Please try again."]})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
