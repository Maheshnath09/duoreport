# DuoReport 📝

A beautiful, production-ready **realtime collaborative report editor** for exactly 2 users. Built with FastAPI, WebSockets, Redis, and modern web technologies.

![DuoReport](https://img.shields.io/badge/Users-Duo%20Only-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green) ![WebSockets](https://img.shields.io/badge/WebSockets-Realtime-orange)

## ✨ Features

- **👥 Duo-Only Mode**: Exactly 2 users per room. Third user gets rejected automatically
- **📄 Document Sections**: Pre-loaded template with Abstract, Introduction, Methodology, Results, Conclusion, References
- **⚡ Realtime Editing**: Instant synchronization using Quill.js deltas and WebSockets
- **👁️ Live Cursors**: See where your collaborator is typing in real-time
- **💾 Auto-Save**: Automatic persistence to Redis every 5 seconds
- **📥 PDF Export**: One-click export with professional formatting using ReportLab
- **🤖 AI Summarization**: Powered by Hugging Face's BART model (free, no API key needed)
- **🌙 Dark Mode**: Beautiful dark theme with smooth transitions
- **📱 Responsive**: Works perfectly on desktop, tablet, and mobile

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Redis server

### Installation

1. **Install Redis** (if not already installed):
   ```bash
   # Windows (using Chocolatey)
   choco install redis-64
   
   # Or download from: https://github.com/microsoftarchive/redis/releases
   ```

2. **Start Redis**:
   ```bash
   redis-server
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

5. **Open your browser**:
   ```
   http://localhost:8000
   ```

## 📖 Usage

### Creating a Room

1. Click **"Create New Room"** on the landing page
2. Enter your name when prompted
3. Share the Room ID with your collaborator
4. Start editing together!

### Joining a Room

1. Get the Room ID from your collaborator
2. Enter it in the **"Join Existing Room"** field
3. Enter your name
4. Click **"Join Room"**

### Editing

- Switch between sections using the sidebar
- Use the rich text toolbar for formatting (bold, italic, lists, etc.)
- Changes sync instantly to your collaborator
- See live cursor positions

### Exporting

- Click **"Export PDF"** in the top navigation
- Download your professionally formatted report

### AI Summarization

- Click **"Summarize"** on any section
- Wait 20-30 seconds for the first request (model loading)
- Summary appears as bullet points in the editor

## 🏗️ Architecture

### Backend (`main.py`)

- **FastAPI**: Async web framework
- **WebSockets**: Realtime bidirectional communication
- **Redis**: Session storage and document persistence
- **ReportLab**: PDF generation
- **Hugging Face API**: AI-powered summarization

### Frontend (`index.html`)

- **Tailwind CSS**: Modern, responsive UI with dark mode
- **Quill.js**: Rich text editor with delta-based sync
- **Vanilla JavaScript**: WebSocket client and UI logic
- **CDN-based**: No build step required

### Key Components

```
┌─────────────────┐
│   Browser 1     │◄──────┐
│   (User 1)      │       │
└────────┬────────┘       │
         │                │
         │ WebSocket      │ Broadcast
         │                │
    ┌────▼────────────────▼───┐
    │   FastAPI Server        │
    │   - ConnectionManager   │
    │   - Auto-save (5s)      │
    └────┬────────────────┬───┘
         │                │
         │ Redis          │ WebSocket
         │                │
    ┌────▼────┐      ┌────▼────────┐
    │  Redis  │      │  Browser 2  │
    │ Storage │      │  (User 2)   │
    └─────────┘      └─────────────┘
```

## 🔧 Configuration

### Session Expiry

Documents expire after **1 hour** of inactivity. Modify in `main.py`:

```python
await redis_client.setex(doc_key, 3600, json.dumps(doc))  # 3600 = 1 hour
```

### Auto-Save Interval

Auto-save runs every **5 seconds**. Modify in `main.py`:

```python
await asyncio.sleep(5)  # Change to desired interval
```

### Max Users Per Room

Currently set to **2 users**. Modify in `main.py`:

```python
if len(self.active_connections[room_id]) >= 2:  # Change limit here
```

## 🧪 Testing

### Manual Test Checklist

1. ✅ **Create Room**: Verify room creation and unique ID generation
2. ✅ **Join Room**: Open in 2 browsers (regular + incognito)
3. ✅ **Duo Limit**: Try joining with a 3rd browser (should be rejected)
4. ✅ **Realtime Sync**: Edit in one browser, verify instant update in other
5. ✅ **Cursor Tracking**: Type in one browser, check cursor status in other
6. ✅ **Auto-Save**: Edit, wait 5s, refresh, verify content persists
7. ✅ **Dark Mode**: Toggle theme, verify smooth transition
8. ✅ **PDF Export**: Export and verify all sections are formatted correctly
9. ✅ **Summarization**: Test AI summary on a section with content
10. ✅ **Disconnect**: Close one browser, verify other continues working

## 📁 Project Structure

```
realtime-document-editor/
├── main.py              # FastAPI backend
├── index.html           # Frontend UI
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🛠️ Technologies

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend Framework | FastAPI | 0.104.1 |
| WebSockets | websockets | 12.0 |
| Database | Redis | 5.0.1 |
| PDF Generation | ReportLab | 4.0.4 |
| HTTP Client | requests | 2.31.0 |
| Frontend CSS | Tailwind CSS | 3.x (CDN) |
| Rich Text Editor | Quill.js | 1.3.6 (CDN) |
| AI Model | BART-large-CNN | Hugging Face |

## 🎨 UI Features

- **Gradient Backgrounds**: Beautiful purple-blue gradients
- **Glass Effects**: Modern glassmorphism design
- **Smooth Animations**: Hover effects and transitions
- **Responsive Layout**: Mobile-first design
- **Dark Mode**: Persistent theme preference
- **Professional Typography**: Clean, readable fonts

## 🔒 Security Considerations

- **No Authentication**: Designed for quick collaboration (add auth for production)
- **Input Sanitization**: HTML stripped for PDF export
- **Session Expiry**: Automatic cleanup after 1 hour
- **CORS**: Currently open (restrict in production)

## 🐛 Troubleshooting

### Redis Connection Error

```
✗ Failed to connect to Redis
```

**Solution**: Ensure Redis is running on `localhost:6379`

```bash
redis-server
```

### WebSocket Connection Failed

**Solution**: Check if the backend is running and accessible

```bash
uvicorn main:app --reload --port 8000
```

### Summarization Timeout

**Solution**: First request may take 20-30 seconds as the model loads. Subsequent requests are faster.

## 📝 Assumptions

1. **Redis**: Running locally on default port (6379)
2. **Network**: Both users on same network or using tunneling (ngrok, etc.) for remote access
3. **Browser**: Modern browser with WebSocket support
4. **Hugging Face API**: Free tier has rate limits; may be slow on first request

## 🚀 Future Enhancements

- [ ] User authentication
- [ ] Persistent database (PostgreSQL)
- [ ] Version history
- [ ] Comments and annotations
- [ ] Export to Word/Markdown
- [ ] Real-time voice chat
- [ ] Mobile app

## 📄 License

MIT License - Feel free to use for your projects!

## 🤝 Contributing

Contributions welcome! This is a production-ready starting point for collaborative editing applications.

---

**Built with ❤️ for seamless duo collaboration**
