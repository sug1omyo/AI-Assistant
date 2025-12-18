"""
Automatic Model Downloader for Stable Diffusion
Downloads lightweight models from HuggingFace on first run
Compatible with GitHub - models are auto-downloaded, not pushed to repo
"""

import os
import sys
from pathlib import Path
from typing import Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ModelDownloader:
    """Auto-download Stable Diffusion models from HuggingFace"""
    
    # Lightweight models that work well
    DEFAULT_MODELS = {
        "sd_base": {
            "name": "runwayml/stable-diffusion-v1-5",
            "type": "checkpoint",
            "size": "~4GB",
            "description": "Stable Diffusion v1.5 - Best balance of quality and speed"
        },
        "vae": {
            "name": "stabilityai/sd-vae-ft-mse",
            "type": "vae",
            "size": "~330MB",
            "description": "VAE for better color accuracy"
        },
        "lora_realism": {
            "name": "SG161222/Realistic_Vision_V5.1_noVAE",
            "type": "lora",
            "size": "~2GB",
            "description": "LoRA for realistic images (optional)"
        }
    }
    
    def __init__(self, models_dir: Optional[Path] = None):
        """
        Initialize model downloader
        
        Args:
            models_dir: Directory to store models (default: models/)
        """
        if models_dir is None:
            # Use directory relative to this script
            self.models_dir = Path(__file__).parent.parent / "models"
        else:
            self.models_dir = Path(models_dir)
        
        # Create subdirectories
        self.checkpoint_dir = self.models_dir / "Stable-diffusion"
        self.vae_dir = self.models_dir / "VAE"
        self.lora_dir = self.models_dir / "Lora"
        
        # Create directories
        for dir_path in [self.checkpoint_dir, self.vae_dir, self.lora_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def is_model_downloaded(self, model_key: str) -> bool:
        """Check if model is already downloaded"""
        model_info = self.DEFAULT_MODELS.get(model_key)
        if not model_info:
            return False
        
        # Determine target directory
        if model_info["type"] == "checkpoint":
            target_dir = self.checkpoint_dir
        elif model_info["type"] == "vae":
            target_dir = self.vae_dir
        else:
            target_dir = self.lora_dir
        
        # Check if directory has content
        if not target_dir.exists():
            return False
        
        # Check for common model files
        model_files = list(target_dir.glob("*.safetensors")) + \
                     list(target_dir.glob("*.ckpt")) + \
                     list(target_dir.glob("*.pt"))
        
        return len(model_files) > 0
    
    def download_from_huggingface(self, model_key: str, force: bool = False) -> bool:
        """
        Download model from HuggingFace Hub
        
        Args:
            model_key: Key from DEFAULT_MODELS
            force: Force re-download even if exists
            
        Returns:
            True if successful, False otherwise
        """
        if model_key not in self.DEFAULT_MODELS:
            logger.error(f"❌ Unknown model: {model_key}")
            return False
        
        model_info = self.DEFAULT_MODELS[model_key]
        
        # Check if already downloaded
        if not force and self.is_model_downloaded(model_key):
            logger.info(f"✅ {model_key} already downloaded")
            return True
        
        logger.info(f"📥 Downloading {model_key}...")
        logger.info(f"   Name: {model_info['name']}")
        logger.info(f"   Type: {model_info['type']}")
        logger.info(f"   Size: {model_info['size']}")
        logger.info(f"   {model_info['description']}")
        
        try:
            # Import here to avoid dependency if not downloading
            from huggingface_hub import snapshot_download
            
            # Determine target directory
            if model_info["type"] == "checkpoint":
                local_dir = self.checkpoint_dir
            elif model_info["type"] == "vae":
                local_dir = self.vae_dir
            else:
                local_dir = self.lora_dir
            
            # Create model-specific subdirectory
            model_name = model_info["name"].split("/")[-1]
            local_dir = local_dir / model_name
            local_dir.mkdir(parents=True, exist_ok=True)
            
            # Download
            logger.info(f"⏳ This may take a while depending on your internet speed...")
            snapshot_download(
                repo_id=model_info["name"],
                local_dir=str(local_dir),
                local_dir_use_symlinks=False,
                resume_download=True
            )
            
            logger.info(f"✅ Successfully downloaded {model_key}")
            logger.info(f"   Saved to: {local_dir}")
            return True
            
        except ImportError:
            logger.error("❌ huggingface_hub not installed!")
            logger.info("💡 Install it: pip install huggingface_hub")
            return False
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            return False
    
    def download_essential_models(self) -> bool:
        """Download essential models for basic functionality"""
        logger.info("=" * 70)
        logger.info("🚀 Stable Diffusion - Auto Model Downloader")
        logger.info("=" * 70)
        logger.info("")
        
        # Download base model (essential)
        logger.info("[1/2] Downloading base Stable Diffusion model...")
        if not self.download_from_huggingface("sd_base"):
            logger.error("❌ Failed to download base model!")
            return False
        
        logger.info("")
        
        # Download VAE (recommended)
        logger.info("[2/2] Downloading VAE for better quality...")
        self.download_from_huggingface("vae")
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ Essential models downloaded successfully!")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Optional: Download LoRA for realistic images")
        logger.info("  Run: python setup_models.py --lora")
        logger.info("")
        
        return True
    
    def get_model_info(self) -> dict:
        """Get information about downloaded models"""
        info = {
            "checkpoints": [],
            "vaes": [],
            "loras": []
        }
        
        # Scan checkpoints
        for model_file in self.checkpoint_dir.rglob("*.safetensors"):
            info["checkpoints"].append({
                "name": model_file.stem,
                "path": str(model_file),
                "size_mb": model_file.stat().st_size / 1024 / 1024
            })
        
        # Scan VAEs
        for model_file in self.vae_dir.rglob("*.safetensors"):
            info["vaes"].append({
                "name": model_file.stem,
                "path": str(model_file),
                "size_mb": model_file.stat().st_size / 1024 / 1024
            })
        
        # Scan LoRAs
        for model_file in self.lora_dir.rglob("*.safetensors"):
            info["loras"].append({
                "name": model_file.stem,
                "path": str(model_file),
                "size_mb": model_file.stat().st_size / 1024 / 1024
            })
        
        return info


def main():
    """Main entry point for standalone usage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Auto-download Stable Diffusion models from HuggingFace"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all models including optional ones"
    )
    parser.add_argument(
        "--lora",
        action="store_true",
        help="Download LoRA for realistic images"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check downloaded models"
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        help="Custom models directory"
    )
    
    args = parser.parse_args()
    
    # Initialize downloader
    downloader = ModelDownloader(
        models_dir=Path(args.models_dir) if args.models_dir else None
    )
    
    # Check mode
    if args.check:
        info = downloader.get_model_info()
        print("\n" + "=" * 70)
        print("📊 Downloaded Models")
        print("=" * 70)
        print(f"\n📦 Checkpoints: {len(info['checkpoints'])}")
        for model in info['checkpoints']:
            print(f"   - {model['name']} ({model['size_mb']:.1f} MB)")
        print(f"\n🎨 VAEs: {len(info['vaes'])}")
        for model in info['vaes']:
            print(f"   - {model['name']} ({model['size_mb']:.1f} MB)")
        print(f"\n✨ LoRAs: {len(info['loras'])}")
        for model in info['loras']:
            print(f"   - {model['name']} ({model['size_mb']:.1f} MB)")
        print("\n" + "=" * 70 + "\n")
        return
    
    # Download essential models
    if not downloader.download_essential_models():
        sys.exit(1)
    
    # Download optional LoRA
    if args.lora or args.all:
        print("\n[OPTIONAL] Downloading LoRA for realistic images...")
        downloader.download_from_huggingface("lora_realism")
    
    # Show summary
    print("\n" + "=" * 70)
    print("🎉 Setup Complete!")
    print("=" * 70)
    print("\nYou can now:")
    print("  1. Start Stable Diffusion: scripts/start-stable-diffusion.bat")
    print("  2. Use text-to-image in ChatBot")
    print("  3. Check models: python setup_models.py --check")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
