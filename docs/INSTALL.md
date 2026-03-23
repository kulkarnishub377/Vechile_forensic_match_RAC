# Installation Guide

Complete installation guide for the Vehicle Re-Identification System.

---

## 📋 Prerequisites

- **Python 3.11+** (3.11.7 recommended)
- **Virtual Environment** (strongly recommended)
- **Disk Space**: ~2GB minimum (5GB recommended)
- **RAM**: 4GB minimum (8GB recommended)
- **Internet Connection** (for model downloads on first run)

---

## 🚀 Quick Install (3 minutes)

### 1️⃣ Clone Repository

```bash
git clone <your-repo-url>
cd _frame_image_finder
```

### 2️⃣ Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Optional Performance Enhancements

```bash
# OpenVINO for CPU optimization (3-5x faster)
pip install openvino

# GPU support (NVIDIA CUDA 11.8+)
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 5️⃣ Start System

```bash
# Method 1: Using startup script
python scripts/start_server.py

# Method 2: Direct uvicorn command
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6️⃣ Verify Installation

Open browser to: **http://localhost:8000**

You should see the Vehicle Re-Identification System interface.

---

## ⚙️ Configuration (Optional)

### Environment Variables

Create `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` for your needs:

```bash
# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Model Configuration
YOLO_BACKEND=pytorch          # or openvino for faster CPU
YOLO_CONF_THRESHOLD=0.3
OSNET_BACKEND=pytorch
USE_OPENVINO=false           # Set to true for faster CPU inference

# Performance
ENABLE_GPU=false             # Auto-detected if CUDA available
MAX_SESSIONS=100
MAX_IMAGES_PER_SESSION=1000

# File Upload
MAX_FILE_SIZE_MB=50

# Matching
MATCH_CONFIDENCE_THRESHOLD=0.85
MATCH_CONFIDENT_LEVEL=0.92
MATCH_PROBABLE_LEVEL=0.85
```

---

## 🔧 Custom Models (Optional)

The system supports custom trained models with automatic fallback:

### Custom Model Locations

Place your custom models in the `models/` folder:

```
models/
├── yolov5_sites_vehicle_v2.pt      # Custom YOLO for vehicles
└── osnet_ain_x1_0_imagenet.pth     # Custom OSNet-AIN ReID model
```

### Auto-Download Fallback

If custom models are not found, the system automatically downloads:
- **YOLOv8n**: From Ultralytics Hub
- **OSNet-AIN**: From TorchReID Hub

**Note**: First run may take 30-60 seconds for model downloads.

---

## 🎯 Verification Steps

### System Health Check

```bash
# Check API health
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
```

### Test Upload & Search

1. **Open Web Interface**: http://localhost:8000
2. **Upload Images**: Click "Select Images" and upload vehicle photos
3. **Search**: Upload a target image and click "Find Matches"
4. **Results**: Should see similarity scores and match types

---

## 🐳 Docker Installation (Alternative)

### Using Docker Compose

```bash
# Clone repository
git clone <your-repo-url>
cd _frame_image_finder

# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Docker Build

```bash
# Build image
docker build -t vehicle-reid-system .

# Run container
docker run -p 8000:8000 vehicle-reid-system

# With custom models (if available)
docker run -p 8000:8000 -v ./models:/app/models vehicle-reid-system
```

---

## 📊 Performance Testing

### Load Test (Optional)

```bash
# Install Apache Bench
sudo apt-get install apache2-utils  # Ubuntu
brew install apache-bench           # macOS

# Test API health endpoint
ab -n 100 -c 10 http://localhost:8000/api/health

# Test upload performance
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/upload \
    -F "file=@test_image_$i.jpg" \
    -H "session_id: test-session"
done
```

---

## 🆘 Troubleshooting

### Issue: Models not loading

```bash
# Check internet connection
ping github.com

# Clear model cache and retry
rm -rf ~/.cache/torch/hub/
rm -rf ~/.cache/torch/

# Restart system
python scripts/start_server.py
```

### Issue: "ModuleNotFoundError: No module named 'torch'"

```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall PyTorch
pip install torch torchvision torchaudio
```

### Issue: High memory usage

```bash
# Reduce session limits in .env
MAX_SESSIONS=50
MAX_IMAGES_PER_SESSION=100

# Restart system
python scripts/start_server.py
```

### Issue: Slow processing

```bash
# Enable OpenVINO optimization
pip install openvino
export USE_OPENVINO=true

# Or use GPU (if available)
export ENABLE_GPU=true
```

### Issue: Port 8000 already in use

```bash
# Find process using port
lsof -i :8000              # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Use different port
export API_PORT=8001
python scripts/start_server.py
```

---

## 🏗️ Development Setup

### Additional Dependencies for Development

```bash
# Install development dependencies
pip install pytest pytest-asyncio black flake8 mypy

# Run tests
pytest tests/ -v

# Code formatting
black app/ tests/ scripts/
flake8 app/ tests/ scripts/

# Type checking
mypy app/
```

### Hot Reload for Development

```bash
# Start with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📚 System Requirements

### Minimum Configuration

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10+, Ubuntu 20.04+, macOS 11+ |
| **Python** | 3.11+ |
| **CPU** | 4 cores |
| **RAM** | 4GB |
| **Disk** | 2GB free space |
| **Network** | Internet for initial model download |

### Recommended Configuration

| Component | Requirement |
|-----------|-------------|
| **CPU** | 8+ cores Intel/AMD |
| **RAM** | 8GB+ |
| **Disk** | 5GB+ NVMe SSD |
| **GPU** | NVIDIA GPU with CUDA (optional) |
| **Network** | 100Mbps+ for faster downloads |

---

## ✅ Success Indicators

After successful installation, you should see:

```bash
✅ Python 3.11+ running
✅ Virtual environment activated
✅ All dependencies installed
✅ Models loaded successfully (custom or downloaded)
✅ API server running on port 8000
✅ Web interface accessible
✅ Health check returns "healthy"
✅ Upload and search working
```

---

## 🌟 Next Steps

1. **Try the System**: Upload vehicle images and test search
2. **Read Documentation**: [Main README](../README.md)
3. **API Integration**: [API Reference](../README.md#api-reference)
4. **Contributing**: [Contributing Guide](CONTRIBUTING.md)
5. **Deployment**: [Deployment Guide](DEPLOYMENT.md)

---

## 💡 Need Help?

### Quick Help
- **Web UI Issue**: Check http://localhost:8000/api/health
- **Model Loading**: Check internet connection and disk space
- **Performance**: Enable OpenVINO with `USE_OPENVINO=true`
- **Memory**: Reduce `MAX_SESSIONS` and `MAX_IMAGES_PER_SESSION`

### Community Support
- 💻 **GitHub Issues**: Report bugs and request features
- 💬 **Discussions**: Ask questions and share ideas
- 📖 **Documentation**: Check `docs/` folder for guides

### System Logs
```bash
# Check application logs (if available)
tail -f logs/app.log

# Check Docker logs
docker-compose logs -f

# Check system resource usage
htop                    # Linux
Activity Monitor        # macOS
Task Manager           # Windows
```

---

**Installation Time**: ~3 minutes
**First Run**: Allow +30s for model downloads
**Ready to Use**: Upload images and start searching! 🚗

---

**Installation Guide Version**: 1.0.0
**Last Updated**: 2026-03-23
