# 🚗 Vehicle Forensic Matching System (Frame Image Finder)

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-red)](https://pytorch.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red)](#license)

**A production-grade intelligent vehicle matching system for toll plaza forensics, leveraging deep learning, computer vision, and multi-modal embeddings to identify matching vehicles across entry and exit transactions.**

---

## 📋 Quick Navigation

- **Getting Started**: [docs/INSTALL.md](docs/INSTALL.md) | [Quick Start](#quick-start)
- **API Guide**: [API Documentation](#api-documentation)
- **Deployment**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Development**: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- **Reference**: [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)

---

## 🎯 Overview

The **Vehicle Forensic Matching System** is an advanced computer vision application designed for toll plaza operations and vehicle forensics. It processes vehicle images from entry and exit points, extracts multi-dimensional embeddings, and uses advanced matching algorithms to identify the same vehicle across different transaction records.

### ✨ Key Capabilities
- ✅ **Multi-Modal Vehicle Matching** - Embedding + OCR + License Plate + Structural validation
- ✅ **Real-Time Processing** - 80-160ms average response time
- ✅ **Production-Ready API** - FastAPI with async processing
- ✅ **Advanced ML Models** - TorchReID (OSNet-AIN), YOLO, PaddleOCR v4
- ✅ **Toll Plaza Forensics** - Entry/exit transaction matching
- ✅ **Fleet Management** - Vehicle tracking and identification

---

## 🏗️ Project Structure

```
d:\_frame_image_finder/                    📦 ROOT
│
├── 📁 app/                                ✨ CORE APPLICATION (v3.0.0)
│   ├── api/                               (REST endpoints & data models)
│   ├── core/                              (ML engines: YOLO, OCR, ReID, Embedding)
│   ├── matching/                          (7 advanced matching algorithms)
│   ├── database/                          (DB operations & queries)
│   ├── services/                          (Business logic)
│   ├── storage/                           (Data & vector management)
│   └── utils/                             (Utilities & helpers)
│
├── 📁 scripts/                            🚀 STARTUP SCRIPTS
│   ├── run_api.py                         (Start FastAPI REST server)
│   └── run_ingestion.py                   (Start background ingestion worker)
│
├── 📁 tools/                              🛠️  UTILITIES & ANALYSIS TOOLS
│   ├── verify_system.py                   (System health & readiness check)
│   ├── monitor_ingestion.py               (Real-time ingestion monitoring)
│   ├── analyze_db.py                      (Database analysis & statistics)
│   ├── check_code.py                      (Code validation & linting)
│   ├── SPEED_COMPARISON.py                (Performance benchmarking)
│   ├── test_full_system.py                (System integration testing)
│   ├── convert_to_openvino.py             (Model optimization for OpenVINO)
│   ├── prepare_reid_classwise.py          (ReID dataset preparation)
│   └── prepare_reid_dataset_standalone.py (Standalone ReID prep tool)
│
├── 📁 notebooks/                          📓 ML TRAINING & EXPERIMENTATION
│   ├── train_vehicle_reid_complete.ipynb  (Complete ReID training pipeline)
│   ├── finetune_vehicle_reid.ipynb        (Fine-tune existing ReID model)
│   └── train_vehicle_reid_colab.ipynb     (Google Colab training setup)
│
├── 📁 configs/                            ⚙️  CONFIGURATION & DEPENDENCIES
│   ├── config.ini                         (Application configuration)
│   └── requirements.txt                   (Python dependencies reference)
│
├── 📁 docs/                               📚 DOCUMENTATION
│   ├── INSTALL.md                         (Installation & setup guide)
│   ├── DEPLOYMENT.md                      (Production deployment guide)
│   ├── CONTRIBUTING.md                    (Contribution guidelines)
│   ├── CODE_OF_CONDUCT.md                 (Community code of conduct)
│   ├── SECURITY.md                        (Security & compliance info)
│   ├── CHANGELOG.md                       (Version history & updates)
│   └── QUICK_REFERENCE.md                 (Configuration & API reference)
│
├── 📁 models/                             🤖 ML MODELS
│   ├── osnet_*.pth                        (ReID models - TorchReID OSNet)
│   ├── yolov5_*.pt                        (Vehicle detection - YOLOv5)
│   ├── PP-OCRv4_*                         (OCR models - PaddleOCR v4)
│   └── yolo26n_site_v3_*                  (Optimized models - OpenVINO)
│
├── 📁 data/                               📊 DATA STORAGE
│   ├── entry_track/                       (Entry transaction data)
│   └── match_results/                     (Matching results)
│
├── 📁 vector_db/                          🔍 VECTOR DATABASE
│   └── *.index                            (FAISS vector indices)
│
├── 📁 tests/                              🧪 UNIT TESTS
│   ├── conftest.py                        (Pytest configuration)
│   ├── test_api.py                        (API tests)
│   └── test_embedding.py                  (Embedding tests)
│
├── 📁 frontend/                           🌐 WEB INTERFACE (Optional)
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
│
├── 📁 preprocessing_service_ref/          📖 REFERENCE IMPLEMENTATIONS
├── 📁 search_service_ref/                 📖 REFERENCE IMPLEMENTATIONS
│
├── 🔧 requirements.txt                    (Python dependencies - MAIN)
├── 📖 README.md                           (This file - START HERE!)
└── .gitignore                             (Git ignore rules)
```

---

## 🚀 Quick Start (5 minutes)

### **1. Install Dependencies**

```bash
cd d:\_frame_image_finder
pip install -r requirements.txt
```

### **2. Review Configuration**

```bash
# Edit configuration (update database credentials, paths, models)
# Location: configs/config.ini
# Key settings: database connection, image paths, ML model backends
```

### **3. Verify System**

```bash
# Check all components working correctly
python tools/verify_system.py
```

### **4. Start Services**

```bash
# Terminal 1: REST API Server (http://localhost:8000)
python scripts/run_api.py

# Terminal 2: Background Ingestion Worker
python scripts/run_ingestion.py

# Terminal 3 (Optional): Monitor Ingestion
python tools/monitor_ingestion.py
```

### **5. Test API**

```bash
# API Documentation: http://localhost:8000/docs
# Health Check:
curl http://localhost:8000/health

# Search for vehicles:
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@vehicle.jpg" \
  -F "plate_text=ABC123"
```

---

## 🌐 API Endpoints

### **POST** `/search` - Find Matching Vehicles

Find vehicles matching the provided image and metadata.

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@entry_vehicle.jpg" \
  -F "plate_text=ABC123" \
  -F "confidence_threshold=0.7"
```

**Response:**
```json
{
  "status": "success",
  "match": {
    "vehicle_id": "VEH_12345",
    "confidence": 0.92,
    "confidence_level": "HIGH",
    "embedding_score": 0.89,
    "ocr_score": 0.95,
    "plate_match": true,
    "timestamp": "2026-03-18T10:30:00Z"
  },
  "processing_time_ms": 145
}
```

### **POST** `/ingest` - Add Vehicle to Database

Ingest a new vehicle image and metadata.

```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@vehicle.jpg" \
  -F "transaction_id=TXN_001" \
  -F "plate_text=XYZ789"
```

### **GET** `/health` - System Health Status

Check if all services are operational.

```bash
curl http://localhost:8000/health
```

Response: `{"status": "healthy", "timestamp": "2026-03-18T10:30:00Z"}`

See [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) for complete API documentation.

---

## 🏗️ System Architecture

```
┌───────────────────────────────────┐
│   CLIENT / WEB DASHBOARD          │
└───────────────┬───────────────────┘
                │
        ┌───────▼────────┐
        │  FASTAPI REST  │
        │  (Port 8000)   │
        └───────┬────────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼─────┐ ┌──▼──────┐ ┌──▼─────┐
│Matching │ │Database │ │ Cache  │
│Engine   │ │ Layer   │ │ Layer  │
├─────────┤ ├─────────┤ ├────────┤
│Embedding│ │SQL Srv  │ │ Redis  │
│OCR Verif│ │Queries  │ │In-Mem  │
│License  │ │Metadata │ │Circuit │
│RANSAC   │ │         │ │Breaker │
└────┬────┘ └────┬────┘ └────────┘
     │           │
┌────▼───────────▼─────────┐
│   FAISS Vector Database  │
│   (5632-D Embeddings)    │
└──────────────────────────┘

┌──────────────────────────┐
│ Background Ingestion     │
├──────────────────────────┤
│ • YOLO Detection         │
│ • OCR Processing         │
│ • Feature Extraction     │
│ • Vector Storage         │
└──────────────────────────┘
```

---

## 💻 Tech Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **API** | FastAPI | 0.100+ | REST endpoints |
| **ML Core** | PyTorch | 2.0+ | Model execution |
| **ReID** | TorchReID OSNet-AIN | 0.2.5+ | Vehicle embeddings |
| **Detection** | YOLOv5/v8 | Latest | Vehicle localization |
| **OCR** | PaddleOCR v4 | 2.7+ | License plate recognition |
| **Vector DB** | FAISS | 1.7.4+ | Similarity search |
| **Database** | SQL Server | Via ODBC | Transaction storage |
| **Cache** | Redis | Latest | Performance optimization |
| **Async** | Uvicorn | Latest | Async server |

---

## 🛠️ Available Tools

### **Startup**
- `scripts/run_api.py` - REST API server
- `scripts/run_ingestion.py` - Background worker

### **Monitoring & Analysis**
- `tools/verify_system.py` - System readiness check
- `tools/monitor_ingestion.py` - Real-time monitoring
- `tools/analyze_db.py` - Database analysis
- `tools/SPEED_COMPARISON.py` - Performance benchmarking

### **ML & Optimization**
- `tools/convert_to_openvino.py` - Model optimization
- `tools/prepare_reid_classwise.py` - ReID dataset prep
- `tools/prepare_reid_dataset_standalone.py` - Standalone prep

### **Testing & Quality**
- `tools/check_code.py` - Code validation
- `tools/test_full_system.py` - Integration testing

### **Training** (Jupyter Notebooks)
- `notebooks/train_vehicle_reid_complete.ipynb` - Complete training
- `notebooks/finetune_vehicle_reid.ipynb` - Transfer learning
- `notebooks/train_vehicle_reid_colab.ipynb` - Cloud training

---

## 📈 Performance Characteristics

### Speed
- **Search Response**: 80-160ms average
- **Ingestion/Vehicle**: 200-400ms
- **Vector Search**: 20-50ms
- **OCR Processing**: 100-150ms

### Accuracy
- **Match Accuracy**: 92-95%
- **False Positive Rate**: < 2%
- **Confidence Calibration**: ±3%

### Throughput
- **Coincident Searches**: 50-100/sec
- **Ingestion Capacity**: 1000+ vehicles/hour
- **Concurrent Users**: 10-50

---

## ⚙️ Configuration

**Location**: `configs/config.ini`

### Critical Settings
```ini
[database]
server = 192.50.20.15          # SQL Server address
database = HTMS_EPE            # Database name
username = admin               # Database user

[reid]
backend = openvino             # CPU-optimized backend
device = CPU                   # Execution device

[yolo]
backend = openvino             # Intel CPU optimization
confidence_threshold = 0.10    # Detection sensitivity

[ocr]
enable = true                  # License plate OCR
backend = paddle               # PaddleOCR backend
```

**Full reference**: See [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)

---

## 📚 Documentation Index

| Document | Topic |
|----------|-------|
| [docs/INSTALL.md](docs/INSTALL.md) | Installation & Setup |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production Deployment |
| [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) | Configuration & APIs |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | Contributing to Project |
| [docs/CODE_OF_CONDUCT.md](docs/CODE_OF_CONDUCT.md) | Community Standards |
| [docs/SECURITY.md](docs/SECURITY.md) | Security & Compliance |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Version History |

---

## 🔐 Security

✅ HTTPS/TLS encryption  
✅ Input validation & sanitization  
✅ Secure credential handling  
✅ Rate limiting & circuit breaker  
✅ CORS policy enforcement  

See [docs/SECURITY.md](docs/SECURITY.md) for details.

---

## 🤝 Contributing

Community contributions welcome! Please review [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

---

## 📄 License

Proprietary - All Rights Reserved

---

## 📞 Getting Help

1. **Setup Issues**: Check [docs/INSTALL.md](docs/INSTALL.md)
2. **Configuration**: See [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)
3. **Deployment**: Review [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
4. **Security**: Read [docs/SECURITY.md](docs/SECURITY.md)

---

## ✅ Latest Version

**v3.0.0** - Production Release (March 2026)

**Key Features:**
- ✨ Modern 8-layer modular architecture
- ✨ 7 advanced matching algorithms
- ✨ TorchReID OSNet-AIN integration
- ✨ OpenVINO optimization support
- ✨ Enhanced monitoring & analytics
- ✨ Professional documentation suite

See [docs/CHANGELOG.md](docs/CHANGELOG.md) for complete history.

---

**Status**: ✅ **Production Ready**  
**Last Updated**: March 18, 2026  
**Maintained By**: Development Team
