# 🛠️ Tools - Analysis, Testing & Utilities

Utility scripts for system monitoring, optimization, and testing.

## Categories

### 📊 Monitoring & Diagnostics

#### **verify_system.py** - System Health Check
Comprehensive system readiness verification.

```bash
python verify_system.py
```

**Checks:**
- ✅ Python version & dependencies
- ✅ Model file existence & integrity
- ✅ Database connectivity
- ✅ FAISS database initialization
- ✅ Configuration validity
- ✅ GPU/CPU availability

**Output**: Detailed report on system status

---

#### **monitor_ingestion.py** - Real-Time Monitoring
Monitor ingestion progress in real-time.

```bash
python monitor_ingestion.py
```

**Displays:**
- Live ingestion statistics
- Processing rates (vehicles/min)
- Queue status
- Error metrics
- Vector count progress

---

#### **analyze_db.py** - Database Analysis
Analyze database performance and content.

```bash
python analyze_db.py
```

**Analyzes:**
- Transaction history
- Image distribution
- Embedding statistics
- Query performance metrics

---

### 🧪 Testing

#### **check_code.py** - Code Quality Validation
Validate code quality and standards.

```bash
python check_code.py
```

**Checks:**
- Python syntax
- Code style (PEP 8)
- Import statements
- Type hints
- Documentation

---

#### **test_full_system.py** - Integration Testing
Run full system integration tests.

```bash
python test_full_system.py
```

**Tests:**
- API endpoints
- Embedding generation
- Matching algorithm
- Database operations
- Cache operations

---

#### **SPEED_COMPARISON.py** - Performance Benchmarking
Compare performance of different backends.

```bash
python SPEED_COMPARISON.py
```

**Benchmarks:**
- PyTorch vs OpenVINO backends
- CPU vs GPU performance
- Different batch sizes
- Cache impact
- Memory utilization

---

### 🤖 ML Model Tools

#### **convert_to_openvino.py** - Model Optimization
Convert models to OpenVINO format for CPU optimization.

```bash
python convert_to_openvino.py
```

**Generates:**
- Optimized ReID model
- Optimized YOLO detector
- Faster inference (3-5x speedup)
- Reduced model size

---

#### **prepare_reid_classwise.py** - ReID Dataset Preparation
Organize and prepare ReID training dataset.

```bash
python prepare_reid_classwise.py
```

**Prepares:**
- Directory structure
- Train/test splits
- Class labels
- Data validation

---

#### **prepare_reid_dataset_standalone.py** - Standalone Preparation
Alternative dataset preparation tool.

```bash
python prepare_reid_dataset_standalone.py
```

**Features:**
- Independent operation
- No external dependencies
- Batch processing support
- Error recovery

---

## Usage Examples

### Quick System Check
```bash
python verify_system.py
```

### Monitor Ingestion (While Running)
```bash
# In separate terminal while run_ingestion.py is active
python monitor_ingestion.py
```

### Benchmark Backends
```bash
python SPEED_COMPARISON.py
# Compares PyTorch vs OpenVINO performance
```

### Prepare Custom Dataset
```bash
python prepare_reid_dataset_standalone.py --input /data/vehicles --output ../models/custom_reid
```

---

## Output Locations

| Tool | Output |
|------|--------|
| verify_system.py | Console report |
| monitor_ingestion.py | Live console display |
| analyze_db.py | JSON/CSV reports |
| SPEED_COMPARISON.py | Performance results |
| Model converters | ../models/openvino/ |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Models not found | Run `verify_system.py` first |
| Connection errors | Check `configs/config.ini` |
| Memory issues | Reduce batch size in config |
| Slow performance | Run `SPEED_COMPARISON.py` to optimize |

---

**Location**: `d:\_frame_image_finder\tools\`  
**Status**: Production Ready (v3.0.0)
