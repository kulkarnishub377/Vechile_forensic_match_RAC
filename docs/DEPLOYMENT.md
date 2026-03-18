# Deployment Guide

Complete guide for deploying the Vehicle Forensic Matching System to production environments.

---

## 📋 Table of Contents

- [Pre-Deployment Checklist](#-pre-deployment-checklist)
- [System Requirements](#-system-requirements)
- [Environment Setup](#-environment-setup)
- [Configuration](#-configuration)
- [Docker Deployment](#-docker-deployment)
- [Kubernetes Deployment](#-kubernetes-deployment)
- [Monitoring](#-monitoring)
- [Troubleshooting](#-troubleshooting)
- [Rollback Procedures](#-rollback-procedures)

---

## ✅ Pre-Deployment Checklist

### Code Quality
- [ ] All tests passing (`pytest tests/ -v`)
- [ ] Code coverage > 80%
- [ ] No security vulnerabilities (`bandit -r app/`)
- [ ] Type checking passes (`mypy app/`)
- [ ] Code formatted (`black app/`)
- [ ] Linting passes (`flake8 app/`)

### Documentation
- [ ] README.md up to date
- [ ] API documentation complete
- [ ] Configuration documented
- [ ] Changelog updated

### Configuration
- [ ] Database credentials configured
- [ ] Redis connection verified
- [ ] Model paths correct
- [ ] Logging paths writable
- [ ] CORS origins configured

### Performance
- [ ] Load testing completed
- [ ] Response times acceptable
- [ ] Memory usage within limits
- [ ] Database connection pool sized
- [ ] Cache hit rate acceptable

### Security
- [ ] No hardcoded passwords
- [ ] API keys rotated
- [ ] SSL/TLS certificates valid
- [ ] Firewall rules configured
- [ ] Database encrypted

---

## 💻 System Requirements

### Minimum Hardware
- **CPU**: 4 cores (8 cores recommended)
- **RAM**: 8GB (16GB recommended)
- **Disk**: 50GB SSD (100GB for production)
- **Network**: 1Gbps Ethernet

### Recommended Hardware (Production)
- **CPU**: 16 cores Intel Xeon
- **RAM**: 32GB DDR4
- **SSD**: 500GB NVMe (separate OS and data)
- **Network**: Redundant 10Gbps

### Software Requirements
- **OS**: Windows Server 2019+ or Ubuntu 20.04 LTS
- **Python**: 3.9+ (3.11 recommended)
- **Database**: SQL Server 2017+
- **Cache**: Redis 6.0+
- **Runtime**: Docker 20.10+ (optional)

---

## 🔧 Environment Setup

### 1. System Packages (Ubuntu)

```bash
sudo apt-get update && sudo apt-get upgrade -y

# Install Python and dependencies
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev

# Install system libraries
sudo apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    libgomp1 \
    graphviz

# Install database client
sudo apt-get install -y unixodbc unixodbc-dev
sudo apt-get install -y odbcinst mssql-tools

# Install Docker (optional)
sudo apt-get install -y docker.io docker-compose
```

### 2. System Packages (Windows)

```powershell
# Using Chocolatey (install Chocolatey first if needed)
choco install python311 -y
choco install git -y
choco install redis -y  # or use WSL2

# Install ODBC Driver for SQL Server
# Download from: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
```

### 3. Directory Structure

```bash
# Create application directories
sudo mkdir -p /opt/frame_image_finder
sudo mkdir -p /var/log/frame_image_finder
sudo mkdir -p /var/lib/frame_image_finder/vector_db
sudo mkdir -p /var/lib/frame_image_finder/cache

# Set permissions
sudo chown -R appuser:appuser /opt/frame_image_finder
sudo chown -R appuser:appuser /var/log/frame_image_finder
sudo chown -R appuser:appuser /var/lib/frame_image_finder
```

### 4. User and Permissions

```bash
# Create dedicated application user
sudo useradd -r -s /bin/bash appuser

# Create log rotation config
sudo tee /etc/logrotate.d/frame_image_finder > /dev/null <<EOF
/var/log/frame_image_finder/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 appuser appuser
    sharedscripts
}
EOF
```

---

## ⚙️ Configuration

### Production config.ini

```ini
[system]
version = 2.6.0
embedding_version = 5632
environment = production
timezone = UTC
log_level = INFO
log_dir = /var/log/frame_image_finder

[database]
server = db-prod.company.com
port = 1433
database = HTMS_EPE
username = ${DB_USERNAME}
password = ${DB_PASSWORD}
driver = ODBC Driver 18 for SQL Server
trust_certificate = no
encrypt = yes
connection_timeout = 30
pool_size = 20
max_overflow = 40
pool_timeout = 30
pool_recycle = 3600

[cache]
redis_host = redis-prod.company.com
redis_port = 6379
redis_password = ${REDIS_PASSWORD}
cache_ttl_seconds = 3600
enable_local_cache = true

[embedding]
yolo_backend = openvino
yolo_openvino_device = CPU
yolo_openvino_precision = FP32
yolo_confidence_threshold = 0.25
yolo_iou_threshold = 0.45
batch_size = 32
num_workers = 8
osnet_model_path = /opt/models/osnet_ibn_x1_0_imagenet.pth

[ocr]
enable_ocr = true
use_paddleocr = true
ocr_confidence_threshold = 0.8

[matching]
enable_ocr_matching = true
uncombined_search_hours = 10
```

### Environment Variables

```bash
# Create .env file
cat > /opt/frame_image_finder/.env << EOF
# Database
DB_USERNAME=prod_user
DB_PASSWORD=$(openssl rand -base64 24)
DB_POOL_SIZE=30

# Cache
REDIS_PASSWORD=$(openssl rand -base64 24)
CACHE_ENABLED=true

# API
API_WORKERS=4
API_HOST=0.0.0.0
API_PORT=8000

# Monitoring
PROMETHEUS_ENABLED=true
LOG_LEVEL=INFO

# Security
SECRET_KEY=$(openssl rand -base64 32)
ALLOWED_ORIGINS=["https://api.company.com"]
EOF

chmod 600 /opt/frame_image_finder/.env
```

---

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", "app.api:app"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DB_USERNAME=${DB_USERNAME}
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/var/log/frame_image_finder
      - ./data:/app/data
      - ./vector_db:/app/vector_db
    depends_on:
      - redis
      - ingestion
    restart: unless-stopped

  ingestion:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DB_USERNAME=${DB_USERNAME}
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/var/log/frame_image_finder
      - ./data:/app/data
      - ./vector_db:/app/vector_db
    command: python -m app.ingestion
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

### Deployment Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Clean up
docker-compose down -v --rmi all
```

---

## ☸️ Kubernetes Deployment

### Deployment Manifest (deployment.yaml)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frame-image-finder
  namespace: production
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: frame-image-finder
  template:
    metadata:
      labels:
        app: frame-image-finder
        version: "2.6.0"
    spec:
      serviceAccountName: frame-image-finder
      containers:
      - name: api
        image: registry.company.com/frame-image-finder:2.6.0
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP
        env:
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        - name: REDIS_HOST
          value: redis-service
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: password
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: logs
          mountPath: /var/log/frame_image_finder
        - name: vector-db
          mountPath: /app/vector_db
      volumes:
      - name: logs
        persistentVolumeClaim:
          claimName: logs-pvc
      - name: vector-db
        persistentVolumeClaim:
          claimName: vector-db-pvc
```

### Service Manifest (service.yaml)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: frame-image-finder-service
  namespace: production
spec:
  type: ClusterIP
  selector:
    app: frame-image-finder
  ports:
  - name: http
    port: 80
    targetPort: http
    protocol: TCP
```

### Ingress Manifest (ingress.yaml)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: frame-image-finder-ingress
  namespace: production
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.company.com
    secretName: frame-image-finder-tls
  rules:
  - host: api.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frame-image-finder-service
            port:
              number: 80
```

---

## 📊 Monitoring

### Prometheus Configuration

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
- job_name: 'frame-image-finder'
  static_configs:
  - targets: ['localhost:8000']
  metrics_path: '/metrics'
```

### Key Metrics to Monitor

```
# Search performance
frame_image_finder_search_duration_seconds
frame_image_finder_search_requests_total
frame_image_finder_matches_found_total

# Resource usage
process_resident_memory_bytes
process_cpu_seconds_total
python_gc_collections_total

# Application health
frame_image_finder_active_requests
frame_image_finder_db_query_duration_seconds
frame_image_finder_cache_hit_ratio
```

### Grafana Dashboard

Create dashboard with panels for:
- Search latency (p50, p95, p99)
- Request rate and errors
- Memory and CPU usage
- Cache hit rate
- Database connection pool
- Vector database size

---

## 🔧 Troubleshooting

### Common Issues

#### Issue: High Memory Usage

```python
# Check cache configuration
# Solution: Enable local cache limits or reduce TTL

# Check FAISS index size
import os
size_mb = os.path.getsize('vector_db/faiss_index.bin') / (1024**2)
print(f"FAISS index: {size_mb}MB")
```

#### Issue: Slow Searches

```bash
# Check backend
curl http://localhost:8000/health | grep yolo_backend

# Solution: Switch to OpenVINO backend
# config.ini: yolo_backend = openvino
```

#### Issue: Database Connection Pool Exhausted

```ini
[database]
pool_size = 30  # Increase
pool_timeout = 60  # Increase
pool_recycle = 1800  # Adjust
```

### Debugging

```bash
# Check application logs
tail -f /var/log/frame_image_finder/api.log

# Check system resources
top -p $(pgrep -f 'python -m app.api')

# Verify database connection
python -c "from app.db import test_connection; test_connection()"

# Check Redis connectivity
redis-cli -a $REDIS_PASSWORD ping

# Monitor FAISS
python scripts/monitor_faiss.py
```

---

## 🔄 Rollback Procedures

### Quick Rollback (to previous version)

```bash
# Stop current version
docker-compose down

# Restore from backup
cp -r backups/2.5.0/* /opt/frame_image_finder/

# Start previous version
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

### Data Rollback

```bash
# Backup current FAISS index
cp vector_db/faiss_index.bin vector_db/faiss_index.bin.backup.v2.6.0

# Restore previous FAISS index
cp backups/faiss_index.bin.v2.5.0 vector_db/faiss_index.bin

# Restart
docker-compose restart api ingestion
```

---

## 📝 Post-Deployment

### Verification Checklist
- [ ] Health check passing
- [ ] API responding to requests
- [ ] Database connected
- [ ] Cache working
- [ ] Logs being written
- [ ] Metrics being collected
- [ ] Performance acceptable
- [ ] No errors in logs

### Monitoring Setup
- [ ] Prometheus scraping metrics
- [ ] Grafana dashboards active
- [ ] Alerting rules configured
- [ ] Log aggregation working
- [ ] Health checks running

---

## 📞 Support

For deployment issues:
- Check logs: `/var/log/frame_image_finder/`
- Review metrics: http://localhost:8000/metrics
- Consult documentation: README.md, SEARCH_API_GUIDE.md
- Contact: forensics@company.com

---

**Last Updated**: 2025-12-26
