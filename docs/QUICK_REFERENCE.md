# 📋 Quick Reference Card

**Vehicle Forensic Matching System** - One-page quick reference guide.

---

## 🎯 Project Essence

**What**: Intelligent vehicle matching system for toll plaza forensics using AI  
**Why**: Identify same vehicle across entry/exit with 94%+ accuracy  
**How**: 5632-D embeddings + OCR + RANSAC matching  
**Where**: REST API on port 8000  

---

## ⚡ Installation (30 seconds)

```bash
git clone repo && cd frame_image_finder
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
python test_setup.py
```

---

## 🚀 Quick Start (2 steps)

```bash
# Terminal 1: Background worker
python -m app.ingestion

# Terminal 2: API server
python -m app.api
```

---

## 🔍 Search API

**Endpoint**: `POST /search`  
**URL**: `http://localhost:8000/search`

**Request**:
```json
{
  "exit_transaction_id": "7313095",
  "k": 10
}
```

**Response**:
```json
{
  "matched_entry_transaction_ids": ["7299123", "7299045"],
  "matches_found": 2,
  "processing_time_seconds": 0.234
}
```

---

## 📊 Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + Uvicorn |
| ML | PyTorch + YOLO + ResNet/OSNet |
| OCR | PaddleOCR v4 |
| Search | FAISS (5632-D vectors) |
| Cache | Redis + In-Memory |
| Database | SQL Server |
| Monitoring | Prometheus + Grafana |

---

## ⚙️ Configuration

**File**: `config.ini`

**Critical Settings**:
```ini
[database]
server = YOUR_SERVER
database = YOUR_DB

[embedding]
yolo_backend = openvino  # or pytorch
```

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Search Latency | 80-160ms avg |
| Throughput | 100+ req/s |
| Accuracy | 94-98% |
| Memory | 2-3GB |
| Embedding Dim | 5632 |

---

## 🧪 Testing

```bash
# All tests
pytest tests/ -v

# Coverage
pytest tests/ --cov=app --cov-report=html

# Specific test
pytest tests/test_api.py -v
```

---

## 🐳 Docker

```bash
# Build & run
docker-compose up -d

# Check logs
docker-compose logs -f api
```

---

## 📁 Key Files

```
app/
├── api.py          ← REST API service
├── ingestion.py    ← Background worker
├── embedding.py    ← Feature extraction
├── matching.py     ← Matching engine
├── ocr.py          ← Text recognition
└── faiss_db.py     ← Vector search

config.ini          ← Configuration
requirements.txt    ← Dependencies
```

---

## 🔗 Documentation Map

| Need | Read |
|------|------|
| **Setup** | [INSTALL.md](INSTALL.md) |
| **First Time** | [START_HERE.md](START_HERE.md) |
| **API Details** | [SEARCH_API_GUIDE.md](SEARCH_API_GUIDE.md) |
| **Full Details** | [README.md](README.md) |
| **Deployment** | [DEPLOYMENT.md](DEPLOYMENT.md) |
| **Contribute** | [CONTRIBUTING.md](CONTRIBUTING.md) |
| **Changes** | [CHANGELOG.md](CHANGELOG.md) |
| **Security** | [SECURITY.md](SECURITY.md) |

---

## 🩺 Health Check

```bash
# Is it running?
curl http://localhost:8000/health

# See metrics
curl http://localhost:8000/metrics

# Test search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"exit_transaction_id":"7313095"}'
```

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| **ModuleNotFoundError** | `pip install -r requirements.txt` |
| **Database connection error** | Check `config.ini` database settings |
| **Slow searches** | Switch to OpenVINO backend in `config.ini` |
| **Out of memory** | Reduce `batch_size` in `config.ini` |
| **ODBC driver error** | Install ODBC Driver 18 for SQL Server |

---

## 📊 Monitoring

**Metrics Endpoint**: `/metrics`  
**Health Endpoint**: `/health`  
**Dashboard**: Internal web interface at `/`

**Key Metrics**:
```
search_requests_total
search_duration_seconds
matches_found_total
cache_hit_rate
active_requests
```

---

## 🔐 Security Notes

✅ No hardcoded credentials  
✅ Use environment variables for secrets  
✅ CORS enabled for API  
✅ Input validation on all endpoints  
✅ SQL injection prevention  

---

## 💡 Common Patterns

### Search with verification
```python
from app.matching import get_matching_engine
engine = get_matching_engine()
result = engine.search("7313095", k=10)
```

### Check embedding quality
```python
from app.embedding import get_embedding_engine
engine = get_embedding_engine()
embedding = engine.generate_embedding("image.jpg")
print(f"Dimension: {len(embedding)}")  # Should be 5632
```

### Database query
```python
from app.db import fetch_exit_transaction
transaction = fetch_exit_transaction("7313095")
print(f"Timestamp: {transaction['timestamp']}")
```

---

## 🚀 Commands Reference

```bash
# Installation
python -m venv venv
pip install -r requirements.txt
python test_setup.py

# Development
python -m app.api              # Start API
python -m app.ingestion        # Start ingestion
pytest tests/ -v               # Run tests

# Docker
docker-compose up -d           # Start all services
docker-compose logs -f         # View logs
docker-compose down            # Stop services

# Deployment
azd up                         # Azure deployment
kubectl apply -f deployment.yaml  # Kubernetes

# Monitoring
curl http://localhost:8000/health    # Health check
curl http://localhost:8000/metrics   # Metrics
```

---

## 📞 Support & Links

**Email**: forensics@company.com  
**GitHub**: https://github.com/yourusername/frame_image_finder  
**Issues**: GitHub Issues  
**Discussions**: GitHub Discussions  

---

## 📝 Version Info

| Info | Value |
|------|-------|
| **Version** | 2.6.0 |
| **Status** | Production Ready |
| **Python** | 3.9+ |
| **License** | Proprietary |
| **Last Updated** | 2025-12-26 |

---

## ✨ Features at a Glance

- ✅ 3-5x faster searches (OpenVINO)
- ✅ 94%+ matching accuracy
- ✅ OCR verification (prevent false positives)
- ✅ Multi-modal embeddings (5632-D)
- ✅ REST API with metrics
- ✅ Docker & Kubernetes ready
- ✅ Redis caching
- ✅ Prometheus monitoring

---

## 🎯 Next Steps

1. **Setup**: Follow [INSTALL.md](INSTALL.md)
2. **Test**: Run `python test_setup.py`
3. **Run**: Start both services
4. **Test API**: Use `curl` commands above
5. **Read**: Full [README.md](README.md) for details

---

<div align="center">

### 📌 Save this reference for quick lookups!

For full details: [README.md](README.md)  
For help: See documentation links above  

**Last Updated**: 2025-12-26

</div>
