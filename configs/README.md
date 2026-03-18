# ⚙️ Configs - Configuration & Dependencies

Application configuration files and Python dependencies management.

## Files

### **config.ini** - Application Configuration

Main configuration file for the entire application.

**Location**: `configs/config.ini`

#### Key Sections

**[system]**
```ini
version = 3.0.0
embedding_version = v512
environment = production
timezone = UTC
```

**[paths]**
```ini
vector_db_path = ../vector_db
models_dir = ../models
data_dir = ../data
logs_dir = logs

enable_path_mapping = true
path_mapping_source = E:\_TrxMedia
path_mapping_target = \\192.50.20.13\_TrxMedia
```

**[database]** (SQL Server)
```ini
server = 192.50.20.15
database = HTMS_EPE
username = admin
driver = ODBC Driver 18 for SQL Server
trust_certificate = yes
encrypt = no

# Connection pooling
pool_size = 20
max_overflow = 40
pool_timeout = 30
pool_recycle = 3600
query_timeout = 30
```

**[reid]** (Vehicle Re-Identification)
```ini
backend = openvino              # torchreid or openvino
checkpoint_path = ../models/reid/custom/osnet_ain_x1_0_custom_final.pth
model_name = osnet_ain_x1_0
image_size = 384
embedding_dim = 512
openvino_path = ../models/reid/openvino/osnet_ain_x1_0_custom.xml
device = CPU
use_gpu = false
```

**[yolo]** (Vehicle Detection)
```ini
backend = openvino
pytorch_model_path = ../models/detection/yolov5n_sites_v3.pt
openvino_model_path = ../models/detection/yolo26n_site_v3_openvino_model
confidence_threshold = 0.10
iou_threshold = 0.4
image_size = 480
```

**[ocr]** (License Plate Recognition)
```ini
enable = true
backend = paddle
rec_model_dir = ../models/ocr_models/PP-OCRv4_mobile_rec_infer_v16
dict_path = ../models/ocr_models/PP-OCRv4_mobile_rec_infer_v16/plate_dict.txt
use_angle_cls = true
lang = en
```

**[cache]** (Performance Optimization)
```ini
enable = true
type = redis              # redis or memory
redis_host = localhost
redis_port = 6379
redis_db = 0
ttl_seconds = 3600
max_memory_mb = 500
```

**[api]** (REST API Server)
```ini
host = 0.0.0.0
port = 8000
workers = 4
timeout = 30
cors_origins = ["*"]
```

**[logging]**
```ini
level = INFO
format = json
max_size_mb = 100
backup_count = 5
```

---

### **requirements.txt** - Python Dependencies

Specifies all required Python packages and versions.

```
fastapi==0.100.0
uvicorn[standard]==0.23.0
torch>=2.0.0
torchvision>=0.15.0
torchreid>=0.2.5
ultralytics>=8.0.0
paddlepaddle==2.6.2
paddleocr==2.7.3
faiss-cpu>=1.7.4
numpy>=1.24.0
opencv-python>=4.8.0
redis>=4.5.0
pymssql>=2.2.0
pydantic>=2.0.0
python-dotenv>=1.0.0
aiofiles>=23.0.0
pip>=23.0
```

---

## Configuration Management

### 1. Edit Configuration

```bash
# Using your preferred editor
# Option 1: Text editor
notepad configs/config.ini

# Option 2: VS Code
code configs/config.ini

# Option 3: Command line
cat configs/config.ini
```

### 2. Critical Settings to Update

**Before running the system:**

```ini
# 1. Database connection
[database]
server = YOUR_SQL_SERVER_IP
database = YOUR_DATABASE_NAME
username = YOUR_USERNAME
# Add password if needed

# 2. Image paths
[paths]
enable_path_mapping = true/false
path_mapping_source = E:\_Images  # Your local path
path_mapping_target = \\SERVER\Images  # Your network path

# 3. API configuration
[api]
host = 0.0.0.0              # Bind to all interfaces
port = 8000                 # Your desired port
```

### 3. Verify Configuration

```bash
# Check configuration validity
python ../tools/verify_system.py
```

---

## Dependency Management

### Install Dependencies

```bash
# Install all dependencies specified in requirements.txt
pip install -r requirements.txt

# Or with specific version control
pip install -r requirements.txt --no-deps
```

### Update Dependencies

```bash
# Update specific package
pip install --upgrade torch

# Update all to latest (with caution)
pip install --upgrade -r requirements.txt
```

### Check Installed Packages

```bash
# List installed packages
pip list

# Show specific package version
pip show torch
```

### Create Custom Requirements

```bash
# Export current environment (careful - may include extra packages)
pip freeze > requirements_snapshot.txt

# Install from custom file
pip install -r requirements_snapshot.txt
```

---

## Environment-Specific Configurations

### Development Configuration

```ini
[system]
environment = development

[logging]
level = DEBUG

[api]
cors_origins = ["*"]
```

### Production Configuration

```ini
[system]
environment = production

[logging]
level = WARNING

[api]
cors_origins = ["https://yourdomain.com"]
workers = 8
```

---

## Troubleshooting

### Configuration Issues

| Issue | Solution |
|-------|----------|
| Database connection fails | Verify server IP, credentials, firewall |
| Models not found | Check `paths/models_dir` in config |
| API port in use | Change `api/port` or kill process |
| Low performance | Adjust `cache` settings, check `backend` type |

### Dependency Issues

| Issue | Solution |
|-------|----------|
| Import error | Run `pip install -r requirements.txt` |
| Version conflict | Check `requirements.txt` for compatible versions |
| CUDA errors | Ensure GPU drivers installed, use CPU backend |
| Memory issues | Reduce batch size in `app/config.py` |

---

## Best Practices

✅ **Do:**
- Keep configs in version control (sample files)
- Use environment variables for sensitive data
- Document custom configuration changes
- Test config changes before production
- Maintain backup of working configs

❌ **Don't:**
- Store passwords in plain config files
- Use development settings in production
- Modify configs while services running
- Share config files with credentials

---

## Reference

**Location**: `d:\_frame_image_finder\configs\`  
**Files**: `config.ini`, `requirements.txt`  
**Status**: Production Ready (v3.0.0)  
**Last Updated**: March 18, 2026

For detailed configuration options, see:
- `configs/config.ini` - All available options
- `../docs/QUICK_REFERENCE.md` - Configuration reference
- `../docs/INSTALL.md` - Installation & setup guide
