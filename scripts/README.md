# 🚀 Scripts - Startup & Operational Commands

Quick start scripts for running the Vehicle Forensic Matching System.

## Available Scripts

### **run_api.py** - REST API Server

Starts the production FastAPI server on port 8000.

```bash
python run_api.py
```

**What it does:**
- Initializes FastAPI application
- Loads models and configuration
- Starts Uvicorn ASGI server
- Enables API documentation at `/docs`

**Environment**: Production-ready

---

### **run_ingestion.py** - Background Ingestion Worker

Starts the background worker that processes new vehicles.

```bash
python run_ingestion.py
```

**What it does:**
- Monitors database for new transactions
- Extracts vehicle images from storage
- Runs object detection (YOLO)
- Performs OCR on license plates
- Generates embeddings
- Stores vectors in FAISS database
- Polls every 10 seconds

**Environment**: Production-ready

---

## Usage

**Standard Deployment** (2 terminals):

```bash
# Terminal 1: API Server
python scripts/run_api.py

# Terminal 2: Ingestion Worker
python scripts/run_ingestion.py
```

**With Monitoring** (3 terminals):

```bash
# Terminal 1: API Server
python scripts/run_api.py

# Terminal 2: Ingestion Worker
python scripts/run_ingestion.py

# Terminal 3: Monitor (optional)
python ../tools/monitor_ingestion.py
```

---

## Configuration

Scripts use settings from: `../configs/config.ini`

Key configuration options:
- Database connection details
- Model paths and backends
- API port (default: 8000)
- Cache settings
- Logging levels

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8000 in use | Change port in config.ini or use different terminal |
| Models not found | Run `python ../tools/verify_system.py` |
| DB connection failed | Check credentials in `configs/config.ini` |
| Low memory | Use OpenVINO backend for faster, lighter models |

---

**Location**: `d:\_frame_image_finder\scripts\`  
**Status**: Production Ready (v3.0.0)
