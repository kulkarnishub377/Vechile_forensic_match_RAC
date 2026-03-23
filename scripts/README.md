# 🚀 Scripts Directory

## Available Scripts

### `start_server.py`
**Purpose:** Launch the Vehicle Re-Identification System web server

**Usage:**
```bash
python scripts/start_server.py
```

**What it does:**
- Starts FastAPI server on `http://0.0.0.0:8000`
- Enables auto-reload for development
- Loads ML models on startup
- Serves frontend UI and API endpoints

**Access:**
- Web UI: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health

---

## Alternative Launch Methods

### Direct Uvicorn Command
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode (No Reload)
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Troubleshooting

**Port already in use:**
```bash
# Change port in start_server.py or use:
python -m uvicorn app.main:app --port 8001
```

**Models not loading:**
```bash
# Check console output for errors
# Models download automatically on first run
# Ensure internet connection for first-time setup
```

---

**Note:** Old scripts (`run_api.py`, `run_ingestion.py`) have been removed as they were for the previous database-dependent system.
