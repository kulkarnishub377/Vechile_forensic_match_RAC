# 📓 Notebooks - ML Training & Experimentation

Jupyter notebooks for vehicle ReID model training, fine-tuning, and experimentation.

## Available Notebooks

### **train_vehicle_reid_complete.ipynb** - Complete Training Pipeline

Comprehensive vehicle ReID model training from scratch.

```bash
jupyter notebook train_vehicle_reid_complete.ipynb
```

**Size**: 28 KB | **Sections**: Complete pipeline

**Covers:**
- Dataset loading and preparation
- Data augmentation strategies
- Model architecture selection
- Training loop with validation
- Loss functions (ArcFace, Triplet, etc.)
- Hyperparameter tuning
- Model evaluation metrics
- Checkpoint saving & loading
- Performance visualization

**Use Case**: Training new ReID model from scratch

**Requirements**:
- Labeled vehicle dataset
- GPU recommended (CUDA)
- 4-8 hours training time
- 8GB+ VRAM minimum

---

### **finetune_vehicle_reid.ipynb** - Transfer Learning & Fine-Tuning

Fine-tune pre-trained ReID model on custom dataset.

```bash
jupyter notebook finetune_vehicle_reid.ipynb
```

**Size**: 22.4 KB | **Sections**: Fine-tuning focus

**Covers:**
- Loading pre-trained OSNet-AIN model
- Freezing backbone layers
- Custom classifier training
- Learning rate scheduling
- Layer-wise unfreezing (progressive)
- Transfer learning best practices
- Evaluation on custom data
- Model export & deployment

**Use Case**: Adapt model to specific vehicle types or dataset

**Requirements**:
- Pre-trained model (provided)
- Custom vehicle dataset (100+ images)
- GPU recommended
- 1-2 hours training time
- 4GB+ VRAM

---

### **train_vehicle_reid_colab.ipynb** - Google Colab Training

Cloud-based training using Google Colab (free GPU).

```bash
# 1. Open notebook in browser
# 2. Open in Google Colab (from Colab menu)
# 3. Run cells sequentially
```

**Size**: 9 KB | **Platform**: Google Colab

**Includes:**
- Data upload from Drive
- GPU allocation & management
- Dependency installation
- Cloud storage integration
- Training with Colab GPUs
- Model download to Drive

**Use Case**: Training without local GPU hardware

**Requirements**:
- Google Account
- Google Drive access
- GPU quota (>30 hours/week free)
- Internet connection

---

## Quick Start

### Local Training (Recommended)

```bash
# 1. Install dependencies
pip install -r ../configs/requirements.txt

# 2. Prepare dataset
python ../tools/prepare_reid_dataset_standalone.py

# 3. Open and run notebook
jupyter notebook train_vehicle_reid_complete.ipynb
```

### Fine-Tuning Existing Model

```bash
# 1. Install dependencies
pip install -r ../configs/requirements.txt

# 2. Prepare custom dataset
python ../tools/prepare_reid_classwise.py

# 3. Open notebook
jupyter notebook finetune_vehicle_reid.ipynb
```

### Cloud Training (Colab)

```bash
# 1. Open notebook in text editor
# 2. Copy content to Google Colab notebook
# 3. Follow Colab-specific instructions
# 4. Run cells (GPU provided free)
```

---

## Dataset Preparation

### Expected Directory Structure

```
training_data/
├── train/
│   ├── vehicle_class_1/
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   └── ...
│   ├── vehicle_class_2/
│   │   └── ...
│   └── ...
│
├── test/
│   ├── vehicle_class_1/
│   │   └── ...
│   └── ...
│
└── val/
    └── ...
```

### Minimum Requirements
- **Minimum images per class**: 20
- **Minimum classes**: 10
- **Train/Test/Val split**: 70/15/15
- **Image format**: JPG (256x256 minimum)
- **Total dataset**: 1000+ images recommended

---

## Training Tips

### Before Training
- ✅ Verify data format with `prepare_reid_dataset_standalone.py`
- ✅ Check GPU availability (`nvidia-smi`)
- ✅ Monitor resource usage during training

### During Training
- 📊 Monitor loss curves in notebook
- 💾 Save best checkpoint regularly
- 🔄 Adjust learning rate if needed
- ⚠️ Watch for overfitting on validation set

### After Training
- ✅ Evaluate on test set
- ✅ Visualize predictions
- ✅ Export model for deployment
- ✅ Save training metrics

---

## Performance Expectations

### Accuracy
- **Vehicle ReID Accuracy**: 85-92% (top-1)
- **mAP (mean Average Precision)**: 60-75%
- **Rank-5 Accuracy**: 95%+

### Speed (per image, after training)
- **PyTorch Backend**: 50-100ms (CPU), 10-20ms (GPU)
- **OpenVINO Backend**: 15-25ms (CPU)

### Resource Usage
- **GPU Memory**: 4-8GB (training), 2GB (inference)
- **CPU Memory**: 4-8GB (training), 1-2GB (inference)
- **Storage**: Model size 50-200MB

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| CUDA out of memory | Reduce batch size in notebook |
| Slow training | Use GPU backend, check GPU utilization |
| Low accuracy | More training data, longer training time |
| Model not converging | Adjust learning rate, check data quality |
| Colab connection lost | Use checkpointing, save to Drive frequently |

---

## Model Export

After training, export model for production:

```python
# In notebook (after training)
import torch

# Save model
torch.save(model.state_dict(), 'trained_reid_model.pth')

# Or use ONNX format
torch.onnx.export(model, input_tensor, 'model.onnx')
```

---

## Next Steps

1. **Prepare your dataset** → Use `prepare_reid_dataset_standalone.py`
2. **Choose training environment**:
   - **Local**: Use `train_vehicle_reid_complete.ipynb`
   - **Transfer Learning**: Use `finetune_vehicle_reid.ipynb`
   - **Cloud**: Use `train_vehicle_reid_colab.ipynb`
3. **Run training** → Follow notebook instructions
4. **Evaluate results** → Check metrics in notebook
5. **Deploy model** → Use optimized version in production

---

**Location**: `d:\_frame_image_finder\notebooks\`  
**Status**: Production Ready (v3.0.0)  
**Last Updated**: March 18, 2026
