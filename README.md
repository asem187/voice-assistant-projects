# Voice Assistant Projects

This repository contains two voice assistant implementations:

1. **`real-voice-assistant/`** - A fully functional voice assistant using real APIs
2. **`realtime-voice-assistant/`** - A concept implementation for future OpenAI Realtime API

## 🚀 Quick Start - Working Voice Assistant

If you want a voice assistant that **works right now**, use the `real-voice-assistant/` project:

```bash
cd real-voice-assistant/
python setup.py
# Edit .env file with your OpenAI API key
python main.py
```

## 📂 Project Comparison

| Feature | real-voice-assistant | realtime-voice-assistant |
|---------|---------------------|-------------------------|
| **Status** | ✅ Fully Working | ⚠️ Concept (Non-functional) |
| **Speech Recognition** | Google Speech API (Free) | WebSocket-based (Fictional) |
| **AI Model** | OpenAI GPT-3.5-turbo (Real) | GPT-4o-realtime (Fictional) |
| **Text-to-Speech** | pyttsx3 (Offline) | Real-time audio streaming |
| **Database** | SQLite (Simple) | PostgreSQL (Advanced) |
| **Architecture** | Simple & Direct | Complex & Scalable |
| **Dependencies** | 9 packages | 34+ packages |
| **Setup Time** | 2 minutes | N/A (Non-functional) |

## 🎯 real-voice-assistant/

### What It Does
- **Listens** to your voice using Google's free speech recognition
- **Thinks** using OpenAI's real Chat API (gpt-3.5-turbo)
- **Remembers** things you tell it in a SQLite database
- **Speaks** back to you using offline text-to-speech
- **Creates tasks** and tracks them persistently

### Features
- ✅ Real-time voice interaction
- ✅ Persistent memory system
- ✅ Task management
- ✅ Function calling capabilities
- ✅ Works offline (except AI processing)
- ✅ No complex setup required

### Requirements
- Python 3.8+
- OpenAI API key
- Microphone and speakers

### Example Interactions
- "Remember that my favorite color is blue"
- "What's my favorite color?"
- "Create a task to buy groceries"
- "Show me my tasks"
- "What time is it?"

## 🔮 realtime-voice-assistant/

### What It Would Do (If It Worked)
- **Real-time bidirectional voice communication** via WebSockets
- **Advanced audio processing** with librosa and numpy
- **Enterprise-grade architecture** with PostgreSQL, Redis, Celery
- **FastAPI web interface** with authentication
- **Comprehensive monitoring** with Prometheus metrics
- **Scalable microservices** design

### Why It Doesn't Work
This project was built for OpenAI's "Realtime API" which **doesn't exist yet**. The implementation is a forward-looking concept of what such a system might look like.

### Technical Highlights
- Asynchronous WebSocket management
- Database connection pooling
- Advanced error handling and reconnection logic
- Audio processing and streaming
- JWT authentication
- Structured logging
- Health checks and metrics

## 🛠️ Installation

### For the Working Version (real-voice-assistant)

```bash
cd real-voice-assistant/
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OpenAI API key
python main.py
```

### For the Concept Version (realtime-voice-assistant)

```bash
cd realtime-voice-assistant/
pip install -r requirements.txt
# This won't work until OpenAI releases a Realtime API
```

## 💰 Cost Breakdown

### real-voice-assistant
- **Speech Recognition**: FREE (Google)
- **Text-to-Speech**: FREE (pyttsx3 offline)
- **Database**: FREE (SQLite)
- **AI Processing**: ~$0.002 per conversation (OpenAI API)

### realtime-voice-assistant
- **Would depend on OpenAI's future Realtime API pricing**
- **Additional costs for PostgreSQL, Redis if using cloud services**

## 🤝 Contributing

### For real-voice-assistant
- Add new voice commands
- Improve speech recognition accuracy
- Add more tool functions
- Enhance memory system

### For realtime-voice-assistant
- Update when OpenAI releases Realtime API
- Improve architecture and patterns
- Add more advanced features
- Convert to use existing APIs as fallback

## 📋 Project Structure

```
voice-assistant-projects/
├── README.md                    # This file
├── real-voice-assistant/        # Working implementation
│   ├── main.py                 # Main voice assistant
│   ├── database.py             # SQLite operations
│   ├── tools.py                # AI function tools
│   ├── requirements.txt        # Dependencies (9 packages)
│   ├── setup.py               # Setup script
│   ├── .env.example           # Environment template
│   └── README.md              # Detailed instructions
└── realtime-voice-assistant/   # Concept implementation
    ├── main.py                # Main application
    ├── config.py              # Configuration management
    ├── models.py              # Database models
    ├── database.py            # PostgreSQL operations
    ├── audio_manager.py       # Audio processing
    ├── openai_client.py       # WebSocket client
    ├── tools.py               # Tool definitions
    ├── requirements.txt       # Dependencies (34+ packages)
    ├── setup.py              # Setup script
    ├── .env.example          # Environment template
    └── README.md             # Project explanation
```

## 🎬 Demo

### Working Demo (real-voice-assistant)
1. Run `python main.py`
2. Say "Remember my name is John"
3. Say "What's my name?"
4. Say "Create a task to call mom"
5. Say "Show me my tasks"

### Concept Demo (realtime-voice-assistant)
- Currently not functional due to fictional API dependency
- Would provide real-time voice streaming when API becomes available

## 🚦 Status

- **real-voice-assistant**: ✅ Production Ready
- **realtime-voice-assistant**: 🚧 Waiting for OpenAI Realtime API

## 📞 Support

If you have issues with:
- **real-voice-assistant**: Check the README, it should work out of the box
- **realtime-voice-assistant**: This is expected to not work until OpenAI releases the Realtime API

## 🔮 Future Plans

1. **When OpenAI releases Realtime API**: Update the concept project to work
2. **Enhanced real-voice-assistant**: Add more features while keeping it simple
3. **Hybrid approach**: Combine the simplicity of the working version with advanced features

---

**Choose your path:**
- Want something that works **now**? → Use `real-voice-assistant/`
- Want to see **future possibilities**? → Explore `realtime-voice-assistant/`
- Want to **contribute**? → Both projects welcome improvements!
