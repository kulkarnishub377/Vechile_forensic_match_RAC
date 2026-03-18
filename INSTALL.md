# Installation Guide

Quick installation guide for the Vehicle Forensic Matching System.

---

## 📋 Prerequisites

- **Python 3.9+** (3.11 recommended)
- **Virtual Environment** (recommended)
- **Disk Space**: ~3GB minimum
- **RAM**: 8GB minimum (16GB recommended)

---

## 🚀 Quick Install (5 minutes)

### 1️⃣ Clone Repository

```bash
git clone https://github.com/yourusername/frame_image_finder.git
cd frame_image_finder
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

### 4️⃣ Install Optional Backends

```bash
# For OpenVINO support (Intel CPU optimization)
pip install openvino openvino-dev

# For OCR support
pip install paddlepaddle paddleocr

# For GPU support (NVIDIA CUDA 11.8)
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 5️⃣ Verify Installation

```bash
python test_setup.py
```

---

## ⚙️ Configuration

### Edit Configuration File

Open `config.ini` and update with your environment:

```ini
[database]
server = YOUR_SQL_SERVER_IP
database = YOUR_DATABASE_NAME
username = YOUR_USERNAME
password = YOUR_PASSWORD

[embedding]
yolo_backend = openvino  # or pytorch
```

---

## ✅ Verify Models

Ensure these files exist in the `models/` directory:

- ✅ `yolov5_sites_vehicle_v2.pt` or `yolo26n_site_v3_openvino_model/`
- ✅ `osnet_ibn_x1_0_imagenet.pth`
- ✅ `PP-OCRv4_mobile_rec_infer_v16/`

---

## 🎯 Next Steps

1. **Read Quick Start**: [START_HERE.md](START_HERE.md)
2. **Learn API**: [SEARCH_API_GUIDE.md](SEARCH_API_GUIDE.md)
3. **Full Documentation**: [README.md](README.md#-table-of-contents)

---

## 🐳 Docker Installation (Alternative)

```bash
# Build image
docker build -t frame-image-finder .

# Run container
docker run -p 8000:8000 frame-image-finder

# With environment file
docker run -p 8000:8000 --env-file .env frame-image-finder
```

---

## 🆘 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'torch'"

```bash
# Solution: Install PyTorch
pip install torch torchvision torchaudio
```

### Issue: "No suitable ODBC driver found"

```bash
# Windows: Install ODBC Driver 18
# Download: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

# Ubuntu/Linux:
sudo apt-get install unixodbc unixodbc-dev
sudo apt-get install mssql-tools
```

### Issue: Database connection failed

```bash
# Verify config.ini with correct credentials
# Check database is accessible from your network
# Test connection:
python -c "from app.db import test_connection; test_connection()"
```

### Issue: Out of memory during ingestion

```ini
# config.ini - Reduce batch size
[ingestion]
batch_size = 50  # decrease from 100
```

---

## 📚 Related Documentation

- **Full README**: [README.md](README.md)
- **Quick Start**: [START_HERE.md](START_HERE.md)
- **API Guide**: [SEARCH_API_GUIDE.md](SEARCH_API_GUIDE.md)
- **Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

---

## ✨ Success Indicators

After installation, you should see:

```bash
✅ Python 3.9+ running
✅ All dependencies installed
✅ Configuration valid
✅ Models found
✅ Database connection working
✅ test_setup.py passes
```

---

## 💡 Need Help?

- Check [Troubleshooting](#-troubleshooting) section
- Review logs: `logs/api.log`
- Email: forensics@company.com

---

**Happy Installation! 🎉**
