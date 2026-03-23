# 🛠️ Tools Directory

## Available Tools

### `convert_to_openvino.py`
**Purpose:** Convert PyTorch models to OpenVINO format for faster CPU inference

**Usage:**
```bash
python tools/convert_to_openvino.py
```

**Benefits:**
- 2-3x faster CPU inference
- Lower memory usage
- Optimized for Intel CPUs

---

### `test_full_system.py`
**Purpose:** Integration testing for the complete vehicle re-ID system

**Usage:**
```bash
python tools/test_full_system.py
```

**Tests:**
- API endpoint functionality
- Model loading and inference
- Upload and search workflows
- Session management

---

### `verify_system.py`
**Purpose:** System health check and verification

**Usage:**
```bash
python tools/verify_system.py
```

**Checks:**
- Python version compatibility
- Required dependencies installed
- Model files accessible
- System resources

---

### `check_code.py`
**Purpose:** Code quality validation

**Usage:**
```bash
python tools/check_code.py
```

---

### `SPEED_COMPARISON.py`
**Purpose:** Performance benchmarking

**Usage:**
```bash
python tools/SPEED_COMPARISON.py --iterations 100
```

---

## Removed Tools

The following tools were removed as they were specific to the old database-dependent system:

- ❌ `analyze_db.py` - Database analysis (no longer needed)
- ❌ `monitor_ingestion.py` - Database ingestion monitoring
- ❌ `prepare_reid_classwise.py` - Dataset preparation for old system
- ❌ `prepare_reid_dataset_standalone.py` - Standalone dataset prep

---

**Location:** `d:\_frame_image_finder\tools\`
**Updated:** March 2026
