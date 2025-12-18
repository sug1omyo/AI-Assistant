# Stable Diffusion Models

**⚠️ Models are NOT included in this repository**

Models are **automatically downloaded** when you run the setup script for the first time.

## Quick Start

```bash
# Auto-download essential models (Base + VAE)
python services/stable-diffusion/setup_models.py

# Optional: Download LoRA for realistic images
python services/stable-diffusion/setup_models.py --lora

# Check downloaded models
python services/stable-diffusion/setup_models.py --check
```

## Default Models

### 🎨 Base Model
- **Name**: `runwayml/stable-diffusion-v1-5`
- **Size**: ~4GB
- **Description**: Stable Diffusion v1.5 - Best balance of quality and speed
- **Auto-downloaded**: ✅ Yes

### 🎨 VAE (Variational Auto-Encoder)
- **Name**: `stabilityai/sd-vae-ft-mse`
- **Size**: ~330MB
- **Description**: Improves color accuracy and image quality
- **Auto-downloaded**: ✅ Yes

### ✨ LoRA (Optional)
- **Name**: `SG161222/Realistic_Vision_V5.1_noVAE`
- **Size**: ~2GB
- **Description**: Realistic image generation
- **Auto-downloaded**: ❌ No (run with --lora flag)

## Directory Structure

```
services/stable-diffusion/models/
├── Stable-diffusion/       # Checkpoint models (.safetensors, .ckpt)
│   └── stable-diffusion-v1-5/
├── VAE/                    # VAE models
│   └── sd-vae-ft-mse/
└── Lora/                   # LoRA models (optional)
    └── Realistic_Vision_V5.1_noVAE/
```

## Why Models Are Not in Git?

1. **Size**: Models are 4-7GB - too large for GitHub
2. **License**: HuggingFace hosts models with proper licensing
3. **Updates**: Easy to update by re-downloading
4. **Bandwidth**: Users download only what they need

## Manual Download (Alternative)

If auto-download doesn't work, manually download from HuggingFace:

1. Visit: https://huggingface.co/runwayml/stable-diffusion-v1-5
2. Download model files
3. Place in `services/stable-diffusion/models/Stable-diffusion/`

## Using Custom Models

1. Download any Stable Diffusion model (.safetensors or .ckpt)
2. Place in `services/stable-diffusion/models/Stable-diffusion/`
3. Restart Stable Diffusion WebUI
4. Select model from dropdown

## Integration with ChatBot

ChatBot's text-to-image feature automatically uses downloaded models:

```python
from services.chatbot.src.utils.image_generator import generate_image_simple

# Generate image
img_bytes = generate_image_simple("a beautiful sunset")

# Save to file
generate_image_simple("a cat in space", output_path="cat.png")
```

## Troubleshooting

### Models not downloading?
```bash
# Install HuggingFace Hub
pip install huggingface_hub

# Re-run setup
python services/stable-diffusion/setup_models.py
```

### Out of disk space?
- Base model only: ~4GB required
- With VAE: ~4.5GB required
- With LoRA: ~6.5GB required

### Slow download?
- Download happens once per model
- Uses HuggingFace CDN (fast worldwide)
- Resume supported if interrupted

## Model Locations

All models are stored in:
```
C:\Users\Asus\Downloads\Compressed\AI-Assistant\services\stable-diffusion\models\
```

This directory is in `.gitignore` - models are never pushed to GitHub.

## Resources

- [HuggingFace Models](https://huggingface.co/models?pipeline_tag=text-to-image)
- [Stable Diffusion Guide](https://stable-diffusion-art.com/)
- [LoRA Models](https://civitai.com/)
