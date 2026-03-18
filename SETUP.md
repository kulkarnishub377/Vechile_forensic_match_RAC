# 🚀 Complete Setup Guide - Frame Image Finder

**Last Updated**: March 18, 2026  
**Status**: ✅ Production Ready

---

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Verification](#verification)
5. [Running Services](#running-services)
6. [Troubleshooting](#troubleshooting)

---

## ✅ Prerequisites

### **Required Software**
- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **SQL Server 2019+** - [Setup Guide](https://docs.microsoft.com/en-us/sql/database-engine/install-windows/install-sql-server)
- **ODBC Driver 18 for SQL Server** - [Download](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- **Git** - [Download](https://git-scm.com/download/win)

### **Optional Software**
- **Redis** - For caching (recommended for production)
- **Visual Studio Code** - Recommended IDE
- **NVIDIA CUDA Toolkit** - Only if using GPU

### **System Requirements**
- **RAM**: 4GB minimum (8GB+ recommended)
- **Disk**: 20GB+ for models and data
- **CPU**: Multi-core processor recommended
- **Network**: Connection to SQL Server

---

## 🔧 Installation

### **Step 1: Clone Repository**

```powershell
# Clone the project
git clone https://github.com/yourusername/frame-image-finder.git
cd frame-image-finder

# Verify directory
dir
```

Expected output:
```
app/
configs/
data/
docs/
models/
scripts/
tools/
frontend/
tests/
notebooks/
README.md
requirements.txt
.env.example
.gitignore
```

### **Step 2: Create Virtual Environment**

**Windows:**
```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Verify activation (should show "venv" prefix)
python --version
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
python --version
```

### **Step 3: Upgrade pip & Install Dependencies**

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# Verify installation
pip list | findstr "torch fastapi pandas"
```

Expected packages:
- ✅ torch ≥ 2.0
- ✅ fastapi ≥ 0.100
- ✅ pandas
- ✅ pyodbc
- ✅ redis
- ✅ opencv-python
- ✅ faiss-cpu / faiss-gpu
- ✅ paddleocr
- ✅ scikit-learn

---

## ⚙️ Configuration

### **Step 1: Create .env File**

```powershell
# Copy template
Copy-Item .env.example .env

# Open in editor
notepad .env
```

### **Step 2: Fill Environment Variables**

Edit `.env` with YOUR values:

```ini
# ⚠️ These MUST be updated with your actual values

# Database
MSSQL_SERVER=your_sql_server_ip       # e.g., 192.168.1.100 or db.example.com
MSSQL_DATABASE=your_database_name      # e.g., VehicleTrackingDB
MSSQL_USERNAME=your_username           # e.g., myuser
MSSQL_PASSWORD=your_secure_password    # ⚠️ Use strong password!

# API
API_PORT=8000
API_HOST=0.0.0.0

# Optional: Image Path Mapping
ENABLE_PATH_MAPPING=false
PATH_MAPPING_SOURCE=E:\_Images
PATH_MAPPING_TARGET=\\server\Images

# Optional: Redis Cache
REDIS_HOST=localhost
REDIS_PORT=6379
```

### **Step 3: Update configs/config.ini**

```powershell
# Open configuration file
notepad configs/config.ini
```

Update these sections:

```ini
[paths]
# Match your .env settings if using path mapping
enable_path_mapping = false

[reid]
backend = openvino              # Use openvino for CPU (faster)
device = CPU

[yolo]
backend = openvino
confidence_threshold = 0.10

[ocr]
enable = true
backend = paddle

[api]
port = 8000
workers = 1

[logging]
level = INFO
```

### **Step 4: Verify File Permissions**

```powershell
# Ensure you can write to logs directory
mkdir -Force logs
mkdir -Force data\cache

# Test write access
"test" | Out-File logs\test.log
if (Test-Path logs\test.log) { 
    Write-Host "✅ Log directory writable"
    Remove-Item logs\test.log
}
```

---

## ✔️ Verification

### **Step 1: Run System Check**

```bash
# Activate virtual environment first
.\venv\Scripts\Activate.ps1  # or: source venv/bin/activate

# Run verification script
python tools/verify_system.py
```

Expected output:
```
✅ Python version: 3.9+
✅ PyTorch installed and working
✅ CUDA: Not available (CPU mode)
✅ Database connection: SUCCESS
✅ FAISS: Loaded successfully
✅ Models: All found
✅ All systems ready!
```

### **Step 2: Test Database Connection**

```bash
python tools/analyze_db.py
```

Expected output:
```
Database Analysis - Vehicle Class Distribution
==============================================
Connected to: HTMS_EPE on 192.50.20.15
Total vehicles: 15,432
```

### **Step 3: Run Integration Tests**

```bash
# Run pytest
pytest tests/ -v

# Or run specific test
pytest tests/test_api.py::test_health -v
```

Expected output:
```
test_api.py::test_health PASSED
test_embedding.py::test_reid_model PASSED
======================== 2 passed in 0.42s ========================
```

---

## 🚀 Running Services

### **Terminal 1: Start REST API**

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start API server
python scripts/run_api.py
```

Expected output:
```
INFO: Started server process [1234]
INFO: Uvicorn running on http://0.0.0.0:8000
INFO: Press CTRL+C to quit
```

**API is now available:**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health**: http://localhost:8000/health

### **Terminal 2: Start Ingestion Worker**

```bash
# Activate virtual environment (new terminal)
.\venv\Scripts\Activate.ps1

# Start ingestion service
python scripts/run_ingestion.py
```

Expected output:
```
INFO: Ingestion worker started
INFO: Polling database every 10 seconds
INFO: Processing batch: 16 vehicles
```

### **Terminal 3: Monitor Ingestion (Optional)**

```bash
# Activate virtual environment (another terminal)
.\venv\Scripts\Activate.ps1

# Monitor progress
python tools/monitor_ingestion.py
```

---

## 🧪 Test API Endpoints

### **Health Check**
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "ready",
  "models": "loaded"
}
```

### **Search for Vehicles**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@vehicle.jpg" \
  -F "plate_text=ABC123"
```

### **Add Vehicle**
```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@vehicle.jpg" \
  -F "transaction_id=TXN_001"
```

---

## 🐛 Troubleshooting

### **Issue: Database Connection Failed**

```bash
# Check credentials
echo $env:MSSQL_SERVER
echo $env:MSSQL_DATABASE

# Test ODBC driver
python -c "import pyodbc; print(pyodbc.drivers())"

# Should show: ODBC Driver 18 for SQL Server

# Test connection
python tools/verify_system.py
```

**Solutions:**
- Verify MSSQL_PASSWORD is set correctly
- Check SQL Server is running: `SELECT 1` in SSMS
- Verify ODBC driver is installed
- Check firewall rules

### **Issue: Out of Memory**

```ini
# In config.ini, reduce:
[ingestion]
worker_threads = 2          # Was 3
batch_size = 8              # Was 16

[faiss]
lazy_load = true            # Enable lazy loading
preload_current = true
max_loaded_partitions = 2   # Was 3
```

Restart ingestion worker after changes.

### **Issue: Slow Search Performance**

```bash
# Check FAISS index
python tools/monitor_ingestion.py

# Check database query time
python tools/SPEED_COMPARISON.py

# Solutions:
# 1. Increase FAISS n_probe
# 2. Enable Redis caching
# 3. Check database indexes
# 4. Use OpenVINO backend (faster CPU)
```

### **Issue: Models Not Loading**

```bash
# Verify model paths
ls models/
ls models/osnet*
ls models/yolov5*

# Check model format
python -c "import torch; torch.load('models/osnet_ain_x1_0_imagenet.pth')"

# If missing, download models:
python tools/download_models.py
```

### **Issue: Python Version Mismatch**

```bash
# Check version
python --version

# Should be 3.9+ (3.10 or 3.11 recommended)

# If wrong version:
# 1. Install Python 3.10+
# 2. Set PATH to new Python first
# 3. Recreate virtual environment
```

---

## 📊 Performance Benchmarking

```bash
# Run performance comparison
python tools/SPEED_COMPARISON.py --iterations 100

# Expected results:
# Search time: 80-160ms
# Ingestion: 200-400ms per vehicle
# Vector search: 20-50ms
```

---

## 🔒 Security Reminders

✅ **DO:**
- Keep `.env` file LOCAL (add to .gitignore)
- Use strong passwords
- Rotate credentials regularly
- Monitor audit logs
- Update dependencies

❌ **DO NOT:**
- Commit `.env` to Git
- Share credentials
- Use default passwords
- Disable security features
- Ignore security warnings

---

## 📚 Next Steps

1. **API Documentation**: See [README.md](README.md)
2. **Configuration Reference**: See [configs/config.ini](configs/config.ini)
3. **Security Policy**: See [SECURITY.md](SECURITY.md)
4. **REST API**: Visit http://localhost:8000/docs
5. **Training Models**: See `notebooks/` directory

---

## ✅ Verification Checklist

- [ ] Python 3.9+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] `.env` file created with values
- [ ] Database connection verified
- [ ] System check passed
- [ ] API server running
- [ ] Ingestion worker running
- [ ] Health check endpoint works
- [ ] Search endpoint tested

---

**Status**: ✅ Setup Complete!

You can now:
- Access API at http://localhost:8000
- Run searches and ingest vehicles
- View logs in `logs/` directory
- Monitor ingestion in Terminal 3

**Questions?** Check logs or review [SECURITY.md](SECURITY.md)

---

**Last Updated**: March 18, 2026  
**Version**: 3.0.0  
**Support**: GitHub Issues or Email
