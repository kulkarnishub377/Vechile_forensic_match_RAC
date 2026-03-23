# Deployment Guide

Complete guide for deploying the Vehicle Re-Identification System to production environments.

---

## 📋 Table of Contents

- [Pre-Deployment Checklist](#-pre-deployment-checklist)
- [System Requirements](#-system-requirements)
- [Environment Setup](#-environment-setup)
- [Configuration](#-configuration)
- [Docker Deployment](#-docker-deployment)
- [Cloud Deployment](#-cloud-deployment)
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
- [ ] CHANGELOG.md updated

### Configuration
- [ ] Model paths configured
- [ ] Logging paths writable
- [ ] CORS origins configured
- [ ] Environment variables set
- [ ] SSL certificates ready (production)

### Performance
- [ ] Load testing completed
- [ ] Response times acceptable (<100ms search)
- [ ] Memory usage within limits
- [ ] Model loading tested
- [ ] Session handling verified

### Security
- [ ] No hardcoded credentials
- [ ] API keys secured
- [ ] SSL/TLS certificates valid
- [ ] Firewall rules configured
- [ ] File upload validation enabled

---

## 💻 System Requirements

### Minimum Hardware
- **CPU**: 4 cores (8 cores recommended)
- **RAM**: 4GB (8GB recommended)
- **Disk**: 10GB SSD (25GB for production)
- **Network**: 100Mbps (1Gbps recommended)

### Recommended Hardware (Production)
- **CPU**: 8+ cores Intel/AMD
- **RAM**: 16GB DDR4
- **SSD**: 100GB NVMe
- **GPU**: Optional NVIDIA GPU for acceleration
- **Network**: Redundant 1Gbps

### Software Requirements
- **OS**: Windows 10+ or Ubuntu 20.04 LTS+
- **Python**: 3.11+ (3.11.7 recommended)
- **Runtime**: Docker 20.10+ (optional)
- **Web Server**: Nginx (optional reverse proxy)

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
    graphviz \
    nginx

# Install Docker (optional)
sudo apt-get install -y docker.io docker-compose-plugin
```

### 2. System Packages (Windows)

```powershell
# Using Chocolatey (install Chocolatey first if needed)
choco install python311 -y
choco install git -y
choco install nginx -y  # optional

# Or use Windows Package Manager
winget install Python.Python.3.11
winget install Git.Git
```

### 3. Directory Structure

```bash
# Create application directories
sudo mkdir -p /opt/vehicle-reid-system
sudo mkdir -p /var/log/vehicle-reid-system
sudo mkdir -p /var/lib/vehicle-reid-system/sessions
sudo mkdir -p /var/lib/vehicle-reid-system/temp

# Set permissions
sudo chown -R appuser:appuser /opt/vehicle-reid-system
sudo chown -R appuser:appuser /var/log/vehicle-reid-system
sudo chown -R appuser:appuser /var/lib/vehicle-reid-system
```

### 4. User and Permissions

```bash
# Create dedicated application user
sudo useradd -r -s /bin/bash appuser

# Create log rotation config
sudo tee /etc/logrotate.d/vehicle-reid-system > /dev/null <<EOF
/var/log/vehicle-reid-system/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 appuser appuser
    sharedscripts
    postrotate
        systemctl reload vehicle-reid-system || true
    endscript
}
EOF
```

---

## ⚙️ Configuration

### Production Environment Variables

```bash
# Create production .env file
cat > /opt/vehicle-reid-system/.env << EOF
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Model Configuration
YOLO_BACKEND=pytorch
YOLO_CONF_THRESHOLD=0.3
OSNET_BACKEND=pytorch
OSNET_EMBEDDING_DIM=512

# Performance Settings
ENABLE_GPU=false  # Set to true if GPU available
USE_OPENVINO=true  # Enable for CPU optimization
FAISS_USE_GPU=false
NUM_WORKERS=4

# Session Management
MAX_SESSIONS=200
MAX_IMAGES_PER_SESSION=500
MAX_SESSION_DURATION_HOURS=24
SESSION_CLEANUP_INTERVAL_MINUTES=30

# File Upload
MAX_FILE_SIZE_MB=50

# Matching Thresholds
MATCH_CONFIDENCE_THRESHOLD=0.85
MATCH_CONFIDENT_LEVEL=0.92
MATCH_PROBABLE_LEVEL=0.85

# Timeouts
DETECTION_TIMEOUT_SECONDS=30
EMBEDDING_TIMEOUT_SECONDS=30
SEARCH_TIMEOUT_SECONDS=10

# Logging
LOG_LEVEL=INFO

# Security (Production)
CORS_ORIGINS=["https://yourdomain.com"]
ENABLE_RATE_LIMITING=true
MAX_REQUESTS_PER_MINUTE=60
EOF

chmod 600 /opt/vehicle-reid-system/.env
```

### Systemd Service (Linux)

```bash
# Create systemd service
sudo tee /etc/systemd/system/vehicle-reid-system.service > /dev/null <<EOF
[Unit]
Description=Vehicle Re-Identification System
After=network.target

[Service]
Type=exec
User=appuser
Group=appuser
WorkingDirectory=/opt/vehicle-reid-system
Environment=PATH=/opt/vehicle-reid-system/venv/bin
ExecStart=/opt/vehicle-reid-system/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable vehicle-reid-system
sudo systemctl start vehicle-reid-system
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
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /app/temp && \
    chown appuser:appuser /app/temp

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  vehicle-reid:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
      - API_WORKERS=4
      - MAX_SESSIONS=200
      - USE_OPENVINO=true
    volumes:
      - ./logs:/var/log/vehicle-reid-system
      - ./temp:/app/temp
      - ./models:/app/models  # Mount custom models if available
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl  # SSL certificates
    depends_on:
      - vehicle-reid
    restart: unless-stopped

volumes:
  logs:
  temp:
```

### Nginx Configuration

```nginx
events {
    worker_connections 1024;
}

http {
    upstream vehicle_reid {
        server vehicle-reid:8000;
    }

    server {
        listen 80;
        server_name yourdomain.com;

        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # File upload size
        client_max_body_size 50M;

        location / {
            proxy_pass http://vehicle_reid;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Timeouts for long-running uploads
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
    }
}
```

---

## ☁️ Cloud Deployment

### AWS ECS (Fargate)

```yaml
# ecs-task-definition.json
{
  "family": "vehicle-reid-system",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "vehicle-reid",
      "image": "your-registry/vehicle-reid:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "LOG_LEVEL", "value": "INFO"},
        {"name": "API_WORKERS", "value": "4"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/vehicle-reid-system",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/api/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

### Google Cloud Run

```yaml
# service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: vehicle-reid-system
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
        run.googleapis.com/memory: "4Gi"
        run.googleapis.com/cpu: "2"
    spec:
      containers:
      - image: gcr.io/project/vehicle-reid:latest
        ports:
        - containerPort: 8000
        env:
        - name: LOG_LEVEL
          value: "INFO"
        - name: API_WORKERS
          value: "1"  # Cloud Run handles scaling
        resources:
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 60
        startupProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 0
          timeoutSeconds: 240
```

---

## 📊 Monitoring

### Health Check Endpoint

The system provides comprehensive health checking:

```bash
# Basic health check
curl http://localhost:8000/api/health

# Expected response
{
  "status": "healthy",
  "models_loaded": true,
  "services": {
    "vehicle_detector": "ready",
    "embedding_generator": "ready",
    "search_engine": "ready",
    "session_manager": "ready"
  },
  "system": {
    "memory_usage_mb": 1024,
    "cpu_percent": 15.2,
    "uptime_seconds": 3600
  }
}
```

### Metrics Collection

```python
# Prometheus metrics available at /metrics
# Key metrics to monitor:

# Request metrics
vehicle_reid_requests_total{method="POST", endpoint="/api/search"}
vehicle_reid_request_duration_seconds{method="POST", endpoint="/api/search"}

# Processing metrics
vehicle_reid_detection_duration_seconds
vehicle_reid_embedding_duration_seconds
vehicle_reid_search_duration_seconds

# System metrics
vehicle_reid_active_sessions
vehicle_reid_total_images
vehicle_reid_memory_usage_bytes
```

### Alerting Rules (Prometheus)

```yaml
groups:
- name: vehicle-reid-alerts
  rules:
  - alert: HighResponseTime
    expr: vehicle_reid_request_duration_seconds{quantile="0.95"} > 5
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"

  - alert: HighMemoryUsage
    expr: vehicle_reid_memory_usage_bytes > 8e9  # 8GB
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Memory usage above threshold"

  - alert: ServiceDown
    expr: up{job="vehicle-reid"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Vehicle ReID service is down"
```

---

## 🔧 Troubleshooting

### Common Issues

#### Issue: Models Not Loading

```bash
# Check model files
ls -la models/
# Should show: yolov5_sites_vehicle_v2.pt, osnet_ain_x1_0_imagenet.pth (if custom)

# Check internet connection for auto-download
curl -I https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt

# Check logs
tail -f /var/log/vehicle-reid-system/app.log | grep -i model
```

#### Issue: High Memory Usage

```bash
# Monitor memory
ps aux | grep python
htop -p $(pgrep -f uvicorn)

# Solution: Reduce session limits
export MAX_SESSIONS=50
export MAX_IMAGES_PER_SESSION=100
```

#### Issue: Slow Processing

```bash
# Enable OpenVINO optimization
export USE_OPENVINO=true

# Check CPU usage
top -p $(pgrep -f uvicorn)

# Monitor processing times
curl http://localhost:8000/metrics | grep duration
```

#### Issue: File Upload Failures

```bash
# Check file size limits
curl -F "file=@large_image.jpg" http://localhost:8000/api/upload
# Increase MAX_FILE_SIZE_MB if needed

# Check disk space
df -h /tmp
df -h /app/temp
```

### Debugging Commands

```bash
# View application logs
journalctl -u vehicle-reid-system -f

# Check service status
systemctl status vehicle-reid-system

# Test API endpoints
curl -X GET http://localhost:8000/api/health
curl -X POST http://localhost:8000/api/upload -F "file=@test.jpg"

# Monitor resource usage
docker stats vehicle-reid-container
```

---

## 🔄 Rollback Procedures

### Quick Rollback (Docker)

```bash
# Stop current deployment
docker-compose down

# Pull previous image
docker pull your-registry/vehicle-reid:v1.9.0

# Update docker-compose.yml to previous version
sed -i 's/vehicle-reid:latest/vehicle-reid:v1.9.0/' docker-compose.yml

# Start previous version
docker-compose up -d

# Verify service
curl http://localhost:8000/api/health
```

### Service Rollback (Systemd)

```bash
# Stop service
sudo systemctl stop vehicle-reid-system

# Restore previous version
sudo cp -r /opt/backups/vehicle-reid-v1.9.0/* /opt/vehicle-reid-system/

# Restart service
sudo systemctl start vehicle-reid-system

# Check status
sudo systemctl status vehicle-reid-system
```

---

## 📝 Post-Deployment

### Verification Checklist
- [ ] Health check returns 200 OK
- [ ] API endpoints respond correctly
- [ ] File upload works
- [ ] Search functionality works
- [ ] Logs are being written
- [ ] Metrics are being collected
- [ ] SSL certificates valid (production)
- [ ] Performance meets requirements

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test health endpoint
ab -n 100 -c 10 http://localhost:8000/api/health

# Test upload endpoint (prepare test images first)
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/upload \
    -F "file=@test_vehicle_$i.jpg" \
    -H "session_id: load-test-session"
done
```

---

## 📞 Support

For deployment issues:
- Check logs: `/var/log/vehicle-reid-system/`
- Review health endpoint: `/api/health`
- Monitor metrics: `/metrics`
- Consult documentation in `docs/` folder
- Open GitHub issue for bugs

---

**Deployment Guide Version**: 1.0.0
**Last Updated**: 2026-03-23
