import torch
import torchreid
import openvino as ov
import os
import onnx

# ================= CONFIGURATION =================
INPUT_PATH = "models/reid/custom/osnet_ain_x1_0_custom_final.pth"  # Updated path
ONNX_PATH = "reid_model.onnx"
OPENVINO_DIR = "models/reid/openvino"
IMAGE_SIZE = (384, 384)
# =================================================

def convert():
    print(f"Starting conversion for {INPUT_PATH}...")

    if not os.path.exists(INPUT_PATH):
        print(f"❌ Error: File {INPUT_PATH} not found!")
        print("Please move the downloaded .pth file to this folder.")
        return

    # 1. Build Model Architecture
    print("1. Building OSNet-AIN model...")
    model = torchreid.models.build_model(
        name='osnet_ain_x1_0',
        num_classes=1000,  # Number of classes doesn't matter for inference features
        loss='softmax',
        pretrained=False
    )
    model.eval()

    # 2. Load Weights
    print(f"2. Loading weights from {INPUT_PATH}...")
    checkpoint = torch.load(INPUT_PATH, map_location='cpu', weights_only=False)
    
    # Handle state_dict format (torchreid saves it under 'state_dict')
    if 'state_dict' in checkpoint:
        state_dict = checkpoint['state_dict']
    else:
        state_dict = checkpoint

    # Remove 'module.' prefix if trained with DataParallel
    new_state_dict = {}
    for k, v in state_dict.items():
        if k.startswith('module.'):
            k = k[7:]
        # Remove classifier layers (we only need features)
        if 'classifier' in k:
            continue
        new_state_dict[k] = v
        
    # Load strictly=False to ignore missing classifier weights
    model.load_state_dict(new_state_dict, strict=False)
    print("Weights loaded successfully!")

    # 3. Export to ONNX
    print("3. Exporting to ONNX...")
    dummy_input = torch.randn(1, 3, IMAGE_SIZE[0], IMAGE_SIZE[1])
    torch.onnx.export(
        model, 
        dummy_input, 
        ONNX_PATH,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}},
        opset_version=11
    )
    print(f"ONNX exported to {ONNX_PATH}")

    # 4. Convert to OpenVINO
    print("4. Converting ONNX to OpenVINO FP16...")
    if not os.path.exists(OPENVINO_DIR):
        os.makedirs(OPENVINO_DIR)
        
    # Initialize OpenVINO Core
    core = ov.Core()
    
    # Read ONNX
    ov_model = core.read_model(ONNX_PATH)
    
    # Serialize (Save) to XML/BIN
    output_xml = os.path.join(OPENVINO_DIR, "osnet_ain_x1_0_custom.xml")
    ov.save_model(ov_model, output_xml, compress_to_fp16=True)
    
    print(f"SUCCESS! OpenVINO model saved to:")
    print(f"   {output_xml}")
    print(f"   {output_xml.replace('.xml', '.bin')}")
    
    # Cleanup
    if os.path.exists(ONNX_PATH):
        os.remove(ONNX_PATH)

if __name__ == "__main__":
    convert()
