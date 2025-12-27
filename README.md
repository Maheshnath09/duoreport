# 📝 DuoReport

<div align="center">

**Realtime Collaborative Report Editor**

A modern, real-time collaborative document editor designed for exactly 2 users to work together seamlessly.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Redis](https://img.shields.io/badge/Redis-7.0+-red.svg)](https://redis.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [Usage](#-usage) • [Tech Stack](#-tech-stack) • [Contributing](#-contributing)

</div>

---

## ✨ Features

### � Real-time Collaboration
- **Instant Synchronization**: See your partner's edits in real-time with zero latency
- **Live Cursor Tracking**: Know exactly where your collaborator is working
- **User Presence**: See who's online and active in the document

### 📄 Rich Text Editing
- **Quill.js Editor**: Professional rich text editing experience
- **Formatting Tools**: Bold, italic, underline, headers, lists, and links
- **Multiple Sections**: Organize your report into Abstract, Introduction, Methodology, Results, Conclusion, and References

### 🎨 Modern UI/UX
- **Dark Mode**: Easy on the eyes with beautiful dark theme support
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices
- **Clean Interface**: Distraction-free writing environment

### 💾 Smart Features
- **Auto-save**: Your work is automatically saved every 5 seconds
- **PDF Export**: Download your completed report as a professional PDF
- **AI Summarization**: Generate quick summaries of your sections (powered by Gemini AI)
- **Redis Persistence**: All documents are safely stored and retrievable

### 🔒 Room-based Collaboration
- **2-User Limit**: Focused collaboration for pairs
- **Unique Room IDs**: Create or join rooms with shareable IDs
- **Session Management**: Automatic cleanup of inactive rooms

---

## 🎬 Demo

### Landing Page
![Landing Page](https://via.placeholder.com/800x500?text=Landing+Page+Screenshot)

### Editor Interface
![Editor Interface](https://via.placeholder.com/800x500?text=Editor+Interface+Screenshot)

### Real-time Collaboration
![Collaboration Demo](https://via.placeholder.com/800x500?text=Real-time+Collaboration+Demo)

---

## 🛠️ Tech Stack

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern, fast web framework for building APIs
- **[WebSockets](https://websockets.readthedocs.io/)** - Real-time bidirectional communication
- **[Redis](https://redis.io/)** - In-memory data store for document persistence
- **[ReportLab](https://www.reportlab.com/)** - PDF generation
- **[Google Gemini AI](https://ai.google.dev/)** - AI-powered text summarization

### Frontend
- **Vanilla JavaScript** - No framework overhead, pure performance
- **[Quill.js](https://quilljs.com/)** - Powerful rich text editor
- **[Tailwind CSS](https://tailwindcss.com/)** - Utility-first CSS framework
- **WebSocket API** - Native browser WebSocket support

---

## � Installation

### Prerequisites
- Python 3.8 or higher
- Redis server
- Node.js and npm (for Tailwind CSS)
- Google Gemini API key (for AI features)

### 1. Clone the Repository
```bash
git clone https://github.com/Maheshnath09/duoreport.git
cd duoreport
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Install Redis
**Windows:**
```bash
# Using Chocolatey
choco install redis-64

# Or download from: https://github.com/microsoftarchive/redis/releases
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

### 4. Set Up Environment Variables
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 5. Build Tailwind CSS
```bash
# Install dependencies
npm install

# Build CSS
npx tailwindcss -i ./src/input.css -o ./static/output.css --minify
```

---

## 🚀 Usage

### Start the Application

1. **Start Redis** (if not already running):
```bash
redis-server
```

2. **Run the FastAPI server**:
```bash
uvicorn main:app --reload --port 8000
```

3. **Open your browser** and navigate to:
```
http://localhost:8000
```

### Creating a Room

1. Click **"Create New Room"** on the landing page
2. Enter your name when prompted
3. Share the **Room ID** with your collaborator
4. Start writing together!

### Joining a Room

1. Get the **Room ID** from your collaborator
2. Enter it in the **"Join Existing Room"** field
3. Enter your name
4. Click **"Join Room"**

### Using the Editor

- **Switch Sections**: Click on section names in the left sidebar
- **Format Text**: Use the toolbar above the editor
- **Export PDF**: Click the "Export PDF" button in the top navigation
- **Summarize**: Click "Summarize" to generate AI summaries
- **Toggle Theme**: Switch between light and dark modes

---

## 📁 Project Structure

```
duoreport/
├── main.py                 # FastAPI application and WebSocket logic
├── index.html             # Frontend HTML
├── static/
│   ├── logo.png          # Application logo
│   └── output.css        # Compiled Tailwind CSS
├── src/
│   └── input.css         # Tailwind CSS source
├── requirements.txt       # Python dependencies
├── package.json          # Node.js dependencies
├── tailwind.config.js    # Tailwind configuration
└── README.md             # This file
```

---

## 🔧 Configuration

### Redis Configuration
By default, the app connects to Redis at `localhost:6379`. To change this, modify the connection in `main.py`:

```python
redis_client = redis.asyncio.Redis(
    host='your-redis-host',
    port=6379,
    decode_responses=True
)
```

### Document Expiration
Documents expire after 1 hour of inactivity. To change this, modify the TTL in `main.py`:

```python
await redis_client.setex(doc_key, 3600, json.dumps(doc))  # 3600 = 1 hour
```

### Room Capacity
Currently limited to 2 users per room. To change this, modify the check in `main.py`:

```python
if len(manager.active_connections[room_id]) >= 2:  # Change 2 to your desired limit
```

---

## 🎨 Customization

### Changing Colors
Edit `tailwind.config.js` to customize the color scheme:

```javascript
theme: {
  extend: {
    colors: {
      primary: '#3b82f6',    // Blue
      secondary: '#8b5cf6',  // Purple
    },
  },
}
```

### Adding Sections
To add more document sections, modify the `TEMPLATE_SECTIONS` in `main.py`:

```python
TEMPLATE_SECTIONS = {
    "abstract": "",
    "introduction": "",
    "methodology": "",
    "results": "",
    "conclusion": "",
    "references": "",
    "your_new_section": ""  # Add your section here
}
```

---

## � Troubleshooting

### WebSocket Connection Failed
- Ensure Redis is running: `redis-cli ping` (should return "PONG")
- Check if port 8000 is available
- Verify firewall settings

### PDF Export Not Working
- Ensure ReportLab is installed: `pip install reportlab`
- Check write permissions in the application directory

### AI Summarization Fails
- Verify your Gemini API key is valid
- Check your API quota and rate limits
- Ensure you have internet connectivity

### Tailwind CSS Not Loading
- Rebuild CSS: `npx tailwindcss -i ./src/input.css -o ./static/output.css --minify`
- Clear browser cache
- Check if `static/output.css` exists

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 for Python code
- Use meaningful commit messages
- Add comments for complex logic
- Test your changes thoroughly

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the amazing web framework
- [Quill.js](https://quilljs.com/) for the rich text editor
- [Tailwind CSS](https://tailwindcss.com/) for the styling framework
- [Redis](https://redis.io/) for data persistence
- [Google Gemini](https://ai.google.dev/) for AI capabilities

---

## 📧 Contact

**Mahesh Nath**
- GitHub: [@Maheshnath09](https://github.com/Maheshnath09)
- Repository: [duoreport](https://github.com/Maheshnath09/duoreport)

---

<div align="center">

**Made with ❤️ for collaborative writing**

⭐ Star this repo if you find it helpful!

</div>
