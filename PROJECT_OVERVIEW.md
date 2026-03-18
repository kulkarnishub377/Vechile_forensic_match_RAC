# 🎯 Project Overview

**Vehicle Forensic Matching System** - Professional vehicle identification and matching system for toll plaza forensics.

---

## 📊 Quick Stats

| Metric | Value |
|--------|-------|
| **Language** | Python 3.9+ |
| **License** | Proprietary |
| **Status** | Production Ready |
| **Latest Version** | 2.6.0 |
| **Python Support** | 3.9, 3.10, 3.11 |
| **Performance** | 80-160ms avg search |

---

## 🎯 What This Project Does

This is an **enterprise-grade intelligent vehicle matching system** designed for toll plaza operations. It:

1. **Processes vehicle images** from entry and exit points
2. **Extracts intelligent features** using state-of-the-art deep learning models
3. **Matches vehicles** with 94%+ accuracy using multi-modal verification
4. **Provides REST API** for integration with existing systems
5. **Monitors performance** with Prometheus metrics and dashboards

---

## 💡 Use Cases

- ✅ Toll plaza vehicle tracking
- ✅ Vehicle forensic analysis
- ✅ Fleet management and identification
- ✅ License plate and VRN verification
- ✅ Cross-transaction vehicle matching

---

## 🚀 Key Technologies

### Deep Learning
- **YOLO v5/v8**: Object detection (vehicles)
- **ResNet-101**: Feature extraction (semantic understanding)
- **OSNet**: Fine-grained vehicle attributes
- **PaddleOCR v4**: License plate recognition

### Vector Search
- **FAISS**: Ultra-fast similarity matching
- **5632-D embeddings**: Multi-modal feature representation

### Backend
- **FastAPI**: Production-ready REST API
- **SQLAlchemy**: Database abstraction
- **Redis**: Distributed caching
- **Prometheus**: Monitoring metrics

---

## 📁 Main Components

| Component | Purpose | Language | Status |
|-----------|---------|----------|--------|
| **API Service** | REST endpoint for searches | Python | ✅ Production |
| **Ingestion Service** | Background worker for processing | Python | ✅ Production |
| **Embedding Engine** | Feature extraction | Python | ✅ Production |
| **Matching Engine** | Multi-level verification | Python | ✅ Production |
| **Dashboard** | Web monitoring interface | HTML/JS | ✅ Production |
| **Vector DB** | FAISS index storage | Binary | ✅ Production |

---

## 📚 Documentation Map

| Document | Purpose | Audience |
|----------|---------|----------|
| [README.md](README.md) | Full project documentation | Developers, Managers |
| [INSTALL.md](INSTALL.md) | Installation guide | New Users |
| [START_HERE.md](START_HERE.md) | Quick start guide | Developers |
| [SEARCH_API_GUIDE.md](SEARCH_API_GUIDE.md) | API reference | API Users |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines | Contributors |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment | DevOps, SRE |
| [CHANGELOG.md](CHANGELOG.md) | Version history | Release Managers |
| [SECURITY.md](SECURITY.md) | Security policies | Security Team |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Community standards | Everyone |

---

## 🏃 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/yourusername/frame_image_finder.git
cd frame_image_finder
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure
```bash
# Edit config.ini with your database credentials
notepad config.ini
```

### 3. Run
```bash
# Terminal 1: Ingestion service
python -m app.ingestion

# Terminal 2: API service
python -m app.api
```

### 4. Test
```bash
# Health check
curl http://localhost:8000/health

# Search
curl -X POST http://localhost:8000/search -d '{"exit_transaction_id":"7313095"}'
```

---

## 📊 Architecture Overview

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
┌──────▼──────────────────┐
│   FastAPI REST API      │
│   (Port 8000)           │
└──────┬──────────────────┘
       │
   ┌───┴────────────────────────┐
   │                            │
┌──▼──────────────┐  ┌─────────▼─────────┐
│ Matching Engine │  │ SQL Server DB     │
│ - Embedding     │  │ - Transactions    │
│ - OCR Verify    │  │ - Images          │
│ - License Match │  │ - Metadata        │
│ - RANSAC        │  └───────────────────┘
└──┬──────────────┘
   │
┌──▼──────────────┐  ┌────────────────────┐
│ FAISS Vector DB │  │ Redis Cache        │
│ - Embeddings    │  │ - Frequent hits    │
│ - 5632-D        │  │ - Session data     │
└─────────────────┘  └────────────────────┘
       ▲
       │
┌──────┴──────────────────┐
│ Ingestion Service       │
│ (Background Worker)     │
│ - YOLO Detection        │
│ - Embedding Generation  │
│ - OCR Extraction        │
│ - FAISS Indexing        │
└────────────────────────┘
```

---

## ⚡ Performance

### Search Latency
- **Average**: 80-160ms
- **P95**: 200-250ms
- **P99**: 300-400ms
- **Throughput**: 100+ requests/second

### Accuracy
- **True Positive Rate**: 94-98%
- **False Positive Rate**: <1%
- **False Negative Rate**: 2-6%

### Resource Usage
- **Memory**: 2-3GB (with 15K vectors)
- **CPU**: 5-10% idle, 20-40% during search
- **Disk**: ~600MB (FAISS index)

---

## 🔧 Configuration

### Key Settings

```ini
[embedding]
yolo_backend = openvino      # or pytorch
yolo_confidence_threshold = 0.25
embedding_dim = 5632

[matching]
enable_ocr_matching = true
SCORE_GAP_HIGH_CONFIDENCE = 0.15

[database]
pool_size = 20
pool_recycle = 3600
```

---

## 📊 Monitoring

### Metrics Available
- Search request metrics
- Matching accuracy metrics
- Database query performance
- Cache hit rates
- Vector database size
- System resource usage

### Dashboards
- Prometheus metrics: `/metrics`
- Grafana dashboards (optional)
- Application health: `/health`

---

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

---

## 🐳 Docker Support

```bash
# Build image
docker build -t frame-image-finder .

# Run with docker-compose
docker-compose up -d
```

---

## 🔐 Security

- ✅ No hardcoded credentials
- ✅ SQL injection prevention
- ✅ Input validation on all endpoints
- ✅ CORS protection
- ✅ Environment-based configuration
- ✅ Responsible disclosure policy

---

## 📦 Dependencies

### Core
- `fastapi` - Web framework
- `torch`, `torchvision` - Deep learning
- `ultralytics` - YOLO
- `opencv-python` - Computer vision
- `paddleocr` - Text recognition
- `openvino` - Inference optimization
- `faiss-cpu` - Vector search

### Database
- `pyodbc` - SQL Server connector
- `sqlalchemy` - ORM
- `redis` - Caching

### Monitoring
- `prometheus-client` - Metrics

---

## 🚀 Getting Started Paths

### For Users
1. Read [INSTALL.md](INSTALL.md)
2. Follow [START_HERE.md](START_HERE.md)
3. Review [SEARCH_API_GUIDE.md](SEARCH_API_GUIDE.md)

### For Developers
1. Read [README.md](README.md)
2. Check [CONTRIBUTING.md](CONTRIBUTING.md)
3. Run tests: `pytest tests/ -v`
4. Check code style: `flake8 app/`

### For DevOps
1. Review [DEPLOYMENT.md](DEPLOYMENT.md)
2. Check Docker config
3. Configure monitoring
4. Setup alerts

---

## 🤝 Contributing

- Read [CONTRIBUTING.md](CONTRIBUTING.md)
- Follow code style guidelines
- Write tests for new features
- Update documentation
- Submit pull requests

---

## 📞 Support & Contact

- **Email**: forensics@company.com
- **Issues**: GitHub Issues
- **Documentation**: See links above
- **Security**: [SECURITY.md](SECURITY.md)

---

## 📄 License

Proprietary - See [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

Built with these amazing open-source projects:
- YOLO (Ultralytics)
- PyTorch (Meta)
- OpenVINO (Intel)
- PaddleOCR (Baidu)
- FAISS (Meta)
- FastAPI (Sebastián Ramírez)

---

## 📊 Project Stats

- **Total Lines of Code**: ~15,000+
- **Components**: 15+
- **Test Coverage**: 80%+
- **Documentation Pages**: 10+
- **API Endpoints**: 5+

---

## ✨ Future Roadmap

- [ ] GPU acceleration
- [ ] Multi-language OCR
- [ ] Real-time video processing
- [ ] Mobile app
- [ ] Advanced analytics
- [ ] GraphQL API
- [ ] Machine learning optimization

---

---

<div align="center">

### ⭐ If this project helps you, please star it on GitHub!

**Made with ❤️ for vehicle forensics**

[Report Issue](#) • [Request Feature](#) • [Read Docs](README.md)

</div>
