# Stable Diffusion Model Auto-Download System

## 🎯 Giải pháp cho vấn đề GitHub model size

### ❌ Vấn đề
- Stable Diffusion models rất lớn (4-7GB)
- GitHub có giới hạn file size (100MB/file, 2GB/repo khuyến nghị)
- GitHub LFS tốn phí cho bandwidth
- Users clone repo không có models

### ✅ Giải pháp
**Auto-download models từ HuggingFace khi setup**

## 📁 Files đã tạo

### 1. Model Downloader
**File**: `services/stable-diffusion/setup_models.py`

**Chức năng**:
- Tự động download models từ HuggingFace Hub
- Support resume download (nếu bị gián đoạn)
- Kiểm tra models đã download chưa (không download lại)
- Download đa dạng models: Checkpoint, VAE, LoRA

**Models mặc định**:
```python
DEFAULT_MODELS = {
    "sd_base": {
        "name": "runwayml/stable-diffusion-v1-5",
        "size": "~4GB",
        "description": "Stable Diffusion v1.5 - Best balance"
    },
    "vae": {
        "name": "stabilityai/sd-vae-ft-mse",
        "size": "~330MB",
        "description": "VAE for better colors"
    },
    "lora_realism": {
        "name": "SG161222/Realistic_Vision_V5.1_noVAE",
        "size": "~2GB",
        "description": "LoRA for realistic images (optional)"
    }
}
```

**Cách dùng**:
```bash
# Download essential models (Base + VAE)
python services/stable-diffusion/setup_models.py

# Download including LoRA
python services/stable-diffusion/setup_models.py --lora

# Check downloaded models
python services/stable-diffusion/setup_models.py --check
```

### 2. ChatBot Image Generator
**File**: `services/chatbot/src/utils/image_generator.py`

**Chức năng**:
- Interface đơn giản để ChatBot tạo ảnh
- Kết nối với Stable Diffusion WebUI API
- Auto-save hoặc return bytes
- Check SD availability trước khi generate

**Cách dùng trong ChatBot**:
```python
from utils.image_generator import generate_image_simple

# Simple usage - just generate
img_bytes = generate_image_simple("a beautiful sunset")

# Generate and save
img_bytes = generate_image_simple(
    "a cat in space",
    output_path=Path("output/cat.png")
)
```

**Advanced usage**:
```python
from utils.image_generator import ImageGenerator

gen = ImageGenerator(api_url="http://127.0.0.1:7860")

# Check if SD is running
if gen.is_available():
    # Generate with custom settings
    img = gen.generate_image(
        prompt="photorealistic portrait",
        negative_prompt="blurry, low quality",
        width=768,
        height=768,
        steps=30,
        cfg_scale=7.5
    )
```

### 3. Setup Scripts

**File**: `scripts/setup-sd-models.bat`
- Windows batch script để setup models
- Auto-install huggingface_hub nếu chưa có
- Gọi setup_models.py

**File**: `scripts/check-sd-models.bat`
- Check models đã download
- Hiển thị size và location

### 4. Documentation

**File**: `services/stable-diffusion/models/README.md`
- Hướng dẫn đầy đủ về model system
- Giải thích tại sao không push models lên Git
- Manual download instructions (backup)
- Integration guide với ChatBot

### 5. Menu Integration

**Updated**: `menu.bat`
- Option **M**: Setup SD Models (Auto-download)
- Option **N**: Check SD Models

## 🚀 Workflow cho End Users

### First Time Setup
```
1. Clone repository
   git clone <repo-url>
   
2. Run menu.bat
   
3. Press M (Setup SD Models)
   - Auto-downloads ~4.5GB models
   - Takes 10-30 mins depending on internet
   
4. Press 6 (Start Stable Diffusion)
   - WebUI starts with downloaded models
   
5. Press 2 (Start ChatBot)
   - Can use text-to-image feature
```

### For Developers
```python
# In your ChatBot code
from utils.image_generator import ImageGenerator

gen = ImageGenerator()

# Check if models are ready
if not gen.is_available():
    print("Start Stable Diffusion first!")
    print("Run: scripts/start-stable-diffusion.bat")
else:
    # Generate!
    img = gen.generate_image("your prompt here")
```

## 📊 Model Directory Structure

```
services/stable-diffusion/models/
├── Stable-diffusion/           # Checkpoints (4GB+)
│   └── stable-diffusion-v1-5/
│       ├── model_index.json
│       ├── v1-5-pruned.safetensors
│       └── ...
├── VAE/                        # VAE models (330MB)
│   └── sd-vae-ft-mse/
│       ├── config.json
│       ├── diffusion_pytorch_model.safetensors
│       └── ...
└── Lora/                       # LoRA (optional, 2GB)
    └── Realistic_Vision_V5.1_noVAE/
        └── ...
```

**✅ Tất cả directories này trong .gitignore**

## 🔒 .gitignore Coverage

Đã có sẵn trong `.gitignore`:
```gitignore
# LARGE FILES & MODELS
**/*.bin
**/*.safetensors
**/*.ckpt
**/*.pt
**/*.pth
**/*.onnx
**/*.h5
**/*.pb

# Keep model config files
!**/*config*.json
!**/config.json
```

Models sẽ **KHÔNG BAO GIỜ** push lên GitHub!

## 💡 Advantages

### Cho Developer
- ✅ Không lo file size limit
- ✅ Không tốn tiền GitHub LFS
- ✅ Repo nhẹ, clone nhanh
- ✅ Models luôn updated từ HuggingFace

### Cho End User
- ✅ Simple: Chỉ cần chạy setup script
- ✅ Automatic: Không cần manual download
- ✅ Resume: Download bị gián đoạn có thể continue
- ✅ Verified: Models từ official HuggingFace repos

### Cho ChatBot Integration
- ✅ Shared models: ChatBot dùng chung với SD WebUI
- ✅ Simple API: `generate_image_simple()` one-liner
- ✅ Smart checking: Auto-detect if SD running
- ✅ Flexible: Custom prompts, sizes, steps, etc.

## 🎯 Recommended Model: SD v1.5

**Chọn `runwayml/stable-diffusion-v1-5` vì**:
1. **Size**: ~4GB (acceptable for one-time download)
2. **Quality**: Production-ready, widely tested
3. **Speed**: Fast generation on consumer hardware
4. **Support**: VAE, LoRA, ControlNet compatible
5. **Community**: Huge ecosystem of resources

**Alternative (nhẹ hơn)**:
- `stabilityai/stable-diffusion-2-1-base` (~5GB but better quality)
- `CompVis/stable-diffusion-v1-4` (~4GB, older version)

## 📝 Next Steps

### Integrate với ChatBot Conversation
```python
# In chatbot/src/chat_handler.py
from utils.image_generator import ImageGenerator

class ChatHandler:
    def __init__(self):
        self.img_gen = ImageGenerator()
    
    def handle_image_request(self, prompt: str):
        if not self.img_gen.is_available():
            return "Stable Diffusion chưa start. Chạy option 6 trong menu!"
        
        # Generate
        img_bytes = self.img_gen.generate_image(prompt)
        
        # Upload to imgbb (existing code)
        from utils.imgbb_uploader import upload_to_imgbb
        url = upload_to_imgbb(img_bytes)
        
        return f"Đã tạo ảnh: {url}"
```

### Add to Setup Script
```bat
REM In scripts/setup-all.bat
echo [7/8] Downloading Stable Diffusion models...
call scripts\setup-sd-models.bat
```

## ✅ Summary

- ✅ **setup_models.py**: Auto-download từ HuggingFace
- ✅ **image_generator.py**: ChatBot text-to-image integration
- ✅ **setup-sd-models.bat**: Windows setup script
- ✅ **check-sd-models.bat**: Verify models
- ✅ **models/README.md**: Full documentation
- ✅ **menu.bat**: Options M & N
- ✅ **.gitignore**: Models excluded

**Giờ users chỉ cần**:
1. Clone repo (nhẹ, không có models)
2. Chạy `menu.bat` → **M** (setup models)
3. Chờ download xong (10-30 phút)
4. Start services và dùng!

🎉 **Vấn đề GitHub model size = SOLVED!**
