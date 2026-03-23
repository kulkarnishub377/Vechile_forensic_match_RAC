# 📋 Quick Reference Card

**Vehicle Re-Identification System** - One-page quick reference guide.

---

## 🎯 Project Essence

**What**: Standalone vehicle re-identification system using deep learning
**Why**: Match vehicles across multiple images with 85%+ accuracy
**How**: YOLO detection + OSNet embeddings + FAISS similarity search
**Where**: Web interface + REST API on port 8000

---

## ⚡ Installation (3 minutes)

```bash
git clone <repo-url> && cd _frame_image_finder
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
python scripts/start_server.py
```

Open: **http://localhost:8000**

---

## 🚀 Quick Start (2 steps)

```bash
# 1. Start system
python scripts/start_server.py

# 2. Open browser
# http://localhost:8000
```

**Web Interface**:
1. Upload vehicle images (Step 1)
2. Upload target image (Step 2)
3. Click "Find Matches"
4. View results with similarity scores

---

## 🔍 API Endpoints

**Base URL**: `http://localhost:8000/api`

**Upload Image**:
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@vehicle.jpg" \
  -H "session_id: my-session"
```

**Search Similar Vehicles**:
```bash
curl -X POST http://localhost:8000/api/search?session_id=my-session&threshold=0.85 \
  -F "file=@target.jpg"
```

**Get Results**:
```bash
curl http://localhost:8000/api/results/my-session
```

**Health Check**:
```bash
curl http://localhost:8000/api/health
```

---

## 📊 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | HTML5, CSS3, Vanilla JS |
| **Backend** | FastAPI + Uvicorn |
| **ML Models** | YOLOv5/v8 + OSNet-AIN |
| **Detection** | Ultralytics YOLO |
| **ReID** | TorchReID (512-D embeddings) |
| **Search** | FAISS IndexFlatL2 |
| **Storage** | In-Memory (Session-based) |
| **Optimization** | OpenVINO (optional) |

---

## ⚙️ Configuration

**File**: `.env` (copy from `.env.example`)

**Critical Settings**:
```bash
# Performance
USE_OPENVINO=true         # 3-5x faster CPU
ENABLE_GPU=false          # Auto-detected

# Models
YOLO_BACKEND=pytorch      # or openvino
OSNET_BACKEND=pytorch

# Limits
MAX_SESSIONS=100
MAX_IMAGES_PER_SESSION=1000
MAX_FILE_SIZE_MB=50

# Matching
MATCH_CONFIDENCE_THRESHOLD=0.85
MATCH_CONFIDENT_LEVEL=0.92
MATCH_PROBABLE_LEVEL=0.85
```

---

## 🧠 Model System

### Smart Model Loading
1. **Custom Models** (Priority):
   - `models/yolov5_sites_vehicle_v2.pt`
   - `models/osnet_ain_x1_0_imagenet.pth`

2. **Auto-Download** (Fallback):
   - YOLOv8n from Ultralytics
   - OSNet-AIN from TorchReID

### Installation
```bash
# Custom models (if available)
mkdir models/
# Place your .pt and .pth files here

# Auto-download triggers on startup if custom models missing
python scripts/start_server.py  # May take 30-60s first run
```

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| **Search Latency** | <100ms avg |
| **Upload Processing** | 80-150ms |
| **Memory Usage** | ~2KB per image |
| **Accuracy** | 85-95% |
| **Embedding Dim** | 512 |
| **Throughput** | 10+ searches/sec |

### Optimization Tips
```bash
# Enable OpenVINO (CPU optimization)
pip install openvino
export USE_OPENVINO=true

# Use GPU (if available)
export ENABLE_GPU=true

# Reduce memory usage
export MAX_SESSIONS=50
export MAX_IMAGES_PER_SESSION=100
```

---

## 🧪 Testing

```bash
# Installation test
curl http://localhost:8000/api/health

# Upload test
curl -X POST http://localhost:8000/api/upload \
  -F "file=@test.jpg" \
  -H "session_id: test"

# Search test
curl -X POST http://localhost:8000/api/search?session_id=test \
  -F "file=@target.jpg"
```

---

## 🐳 Docker

```bash
# Docker Compose (recommended)
docker-compose up -d

# Check logs
docker-compose logs -f

# Single container
docker build -t vehicle-reid .
docker run -p 8000:8000 vehicle-reid
```

---

## 📁 Key Files

```
_frame_image_finder/
├── app/
│   ├── main.py              ← FastAPI app
│   ├── config.py            ← Configuration
│   └── services/
│       ├── vehicle_detector.py    ← YOLO detection
│       ├── embedding_generator.py ← OSNet embeddings
│       ├── search_engine.py       ← FAISS search
│       ├── session_manager.py     ← Session handling
│       └── image_storage.py       ← Image storage
├── frontend/
│   ├── index.html           ← Web interface
│   ├── css/style.css        ← Modern styling
│   └── js/app.js            ← JavaScript logic
├── scripts/
│   └── start_server.py      ← Startup script
├── requirements.txt         ← Dependencies
└── .env.example            ← Configuration template
```

---

## 🔗 Documentation Map

| Need | Read |
|------|------|
| **Setup** | [INSTALL.md](INSTALL.md) |
| **Full Details** | [README.md](../README.md) |
| **API Reference** | [README.md#api-reference](../README.md#api-reference) |
| **Deployment** | [DEPLOYMENT.md](DEPLOYMENT.md) |
| **Contributing** | [CONTRIBUTING.md](CONTRIBUTING.md) |
| **Changes** | [CHANGELOG.md](CHANGELOG.md) |
| **Security** | [SECURITY.md](SECURITY.md) |

---

## 🩺 Health Check

```bash
# System health
curl http://localhost:8000/api/health

# Expected response:
{
  "status": "healthy",
  "models_loaded": true,
  "services": {
    "vehicle_detector": "ready",
    "embedding_generator": "ready",
    "search_engine": "ready",
    "session_manager": "ready"
  }
}

# Web interface
curl http://localhost:8000/
```

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| **Models not loading** | Check internet connection, restart system |
| **ModuleNotFoundError** | `pip install -r requirements.txt` |
| **Port 8000 in use** | `export API_PORT=8001` |
| **High memory usage** | Reduce `MAX_SESSIONS` and `MAX_IMAGES_PER_SESSION` |
| **Slow processing** | `pip install openvino` and `export USE_OPENVINO=true` |
| **Upload failures** | Check file size (<50MB) and format (JPG/PNG/BMP/WEBP) |

---

## 📊 Match Results

### Match Types
- 🟢 **Confident** (≥90% similarity) - Very likely same vehicle
- 🟡 **Probable** (85-90% similarity) - Likely same vehicle
- 🟠 **Weak** (threshold-85% similarity) - Possible match

### Response Format
```json
{
  "matches": [
    {
      "image_id": "uuid",
      "filename": "car1.jpg",
      "match_score": 0.92,
      "match_type": "confident",
      "upload_time": "2025-03-23T12:00:00"
    }
  ],
  "total_matches": 1,
  "search_time_ms": 87.5
}
```

---

## 🔐 Security Notes

✅ **No Database Required** - All data in-memory
✅ **Session Isolation** - Each session independent
✅ **File Validation** - Type and size checking
✅ **No Persistent Storage** - Data cleared on restart
✅ **MIT Licensed** - Open source ready

### Security Best Practices
```bash
# Use HTTPS in production
# Set up reverse proxy (nginx)
# Configure firewall rules
# Regular security updates
```

---

## 💡 Common Usage Patterns

### Web Interface Workflow
```
1. Open http://localhost:8000
2. Upload database images (drag & drop)
3. Upload target image
4. Adjust threshold (default 85%)
5. Click "Find Matches"
6. Review results with confidence scores
```

### API Integration
```python
import requests

# Upload images
files = {'file': open('vehicle.jpg', 'rb')}
response = requests.post(
    'http://localhost:8000/api/upload',
    files=files,
    headers={'session_id': 'my-session'}
)

# Search for matches
target = {'file': open('target.jpg', 'rb')}
response = requests.post(
    'http://localhost:8000/api/search?session_id=my-session&threshold=0.85',
    files=target
)
matches = response.json()
```

### Session Management
```bash
# Create session by uploading first image
# Add more images with same session_id
# Search within that session only
# Clear session when done
curl -X POST http://localhost:8000/api/clear/my-session
```

---

## 🚀 Commands Reference

```bash
# Installation
python -m venv venv
pip install -r requirements.txt

# Development
python scripts/start_server.py       # Start system
python -m uvicorn app.main:app --reload  # Hot reload

# Docker
docker-compose up -d                 # Start with Docker
docker-compose logs -f               # View logs
docker-compose down                  # Stop services

# Testing
curl http://localhost:8000/api/health     # Health check
curl http://localhost:8000/              # Web interface

# Performance
export USE_OPENVINO=true            # Enable CPU optimization
export ENABLE_GPU=true              # Enable GPU (if available)
```

---

## 📞 Support & Links

**GitHub**: Repository Issues and Discussions
**Documentation**: `docs/` folder
**Support**: GitHub Issues for bugs, Discussions for questions

---

## 📝 Version Info

| Info | Value |
|------|-------|
| **Version** | 1.0.0 |
| **Status** | Production Ready |
| **Python** | 3.11+ |
| **License** | MIT |
| **Last Updated** | 2026-03-23 |

---

## ✨ Features at a Glance

- ✅ **No Database Required** - Standalone system
- ✅ **Smart Model Loading** - Custom + auto-download fallback
- ✅ **Session-Based** - Upload and search in isolated sessions
- ✅ **Modern Web UI** - Professional glass morphism design
- ✅ **Fast Search** - <100ms typical response time
- ✅ **Multiple Formats** - JPG, PNG, BMP, WEBP support
- ✅ **RESTful API** - Easy integration with other systems
- ✅ **Docker Ready** - Complete containerization
- ✅ **Open Source** - MIT licensed

---

## 🎯 Next Steps

1. **Install**: Follow commands above or [INSTALL.md](INSTALL.md)
2. **Test**: Open http://localhost:8000 and upload images
3. **Integrate**: Use API endpoints for programmatic access
4. **Deploy**: See [DEPLOYMENT.md](DEPLOYMENT.md) for production
5. **Contribute**: Check [CONTRIBUTING.md](CONTRIBUTING.md)

---

<div align="center">

### 📌 Bookmark this reference for quick lookups!

For complete details: [README.md](../README.md)
For setup help: Follow installation commands above

**System Type**: Vehicle Re-Identification (Standalone)
**Last Updated**: 2026-03-23

</div>
