"""
Text-to-Image Generator for ChatBot
Integrates with Stable Diffusion WebUI API
Lightweight interface for generating images from text prompts
"""

import os
import requests
import base64
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Generate images using Stable Diffusion via WebUI API"""
    
    def __init__(self, api_url: str = "http://127.0.0.1:7860"):
        """
        Initialize image generator
        
        Args:
            api_url: URL of Stable Diffusion WebUI API
        """
        self.api_url = api_url.rstrip("/")
        self.timeout = 300  # 5 minutes for image generation
    
    def is_available(self) -> bool:
        """Check if Stable Diffusion API is available"""
        try:
            response = requests.get(
                f"{self.api_url}/sdapi/v1/options",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"SD API not available: {e}")
            return False
    
    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        cfg_scale: float = 7.0,
        seed: int = -1,
        sampler_name: str = "Euler a"
    ) -> Optional[bytes]:
        """
        Generate image from text prompt
        
        Args:
            prompt: Text description of desired image
            negative_prompt: What to avoid in the image
            width: Image width (default 512)
            height: Image height (default 512)
            steps: Sampling steps (default 20, higher = better quality but slower)
            cfg_scale: CFG Scale (default 7.0, higher = closer to prompt)
            seed: Random seed (-1 for random)
            sampler_name: Sampling method
            
        Returns:
            Image bytes (PNG format) or None if failed
        """
        if not self.is_available():
            logger.error("❌ Stable Diffusion API not available!")
            logger.info("💡 Start it: scripts/start-stable-diffusion.bat")
            return None
        
        # Prepare request
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "seed": seed,
            "sampler_name": sampler_name,
            "save_images": False,  # Don't save to disk
            "send_images": True,   # Return in response
        }
        
        try:
            logger.info(f"🎨 Generating image: {prompt[:50]}...")
            
            # Send request
            response = requests.post(
                f"{self.api_url}/sdapi/v1/txt2img",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.error(f"❌ API error: {response.status_code}")
                return None
            
            # Extract image
            result = response.json()
            if "images" not in result or len(result["images"]) == 0:
                logger.error("❌ No images in response")
                return None
            
            # Decode base64 image
            image_b64 = result["images"][0]
            image_bytes = base64.b64decode(image_b64)
            
            logger.info(f"✅ Image generated ({len(image_bytes)} bytes)")
            return image_bytes
            
        except requests.Timeout:
            logger.error("❌ Request timeout - image generation took too long")
            return None
        except Exception as e:
            logger.error(f"❌ Generation failed: {e}")
            return None
    
    def generate_and_save(
        self,
        prompt: str,
        output_path: Path,
        **kwargs
    ) -> bool:
        """
        Generate image and save to file
        
        Args:
            prompt: Text description
            output_path: Where to save image
            **kwargs: Additional generation parameters
            
        Returns:
            True if successful, False otherwise
        """
        # Generate
        image_bytes = self.generate_image(prompt, **kwargs)
        if not image_bytes:
            return False
        
        # Save
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            
            logger.info(f"💾 Saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save: {e}")
            return False
    
    def get_models(self) -> list[str]:
        """Get list of available models"""
        try:
            response = requests.get(
                f"{self.api_url}/sdapi/v1/sd-models",
                timeout=5
            )
            if response.status_code == 200:
                models = response.json()
                return [m["title"] for m in models]
            return []
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return []
    
    def set_model(self, model_name: str) -> bool:
        """Switch to different model"""
        try:
            payload = {
                "sd_model_checkpoint": model_name
            }
            response = requests.post(
                f"{self.api_url}/sdapi/v1/options",
                json=payload,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to set model: {e}")
            return False


# Quick helper function for simple usage
def generate_image_simple(
    prompt: str,
    output_path: Optional[Path] = None,
    api_url: str = "http://127.0.0.1:7860"
) -> Optional[bytes]:
    """
    Simple one-liner for image generation
    
    Args:
        prompt: What to generate
        output_path: Optional file to save to
        api_url: Stable Diffusion API URL
        
    Returns:
        Image bytes or None
        
    Example:
        # Just generate and get bytes
        img = generate_image_simple("a beautiful sunset")
        
        # Generate and save
        img = generate_image_simple(
            "a beautiful sunset",
            output_path=Path("sunset.png")
        )
    """
    gen = ImageGenerator(api_url)
    
    if output_path:
        success = gen.generate_and_save(prompt, output_path)
        if success:
            with open(output_path, "rb") as f:
                return f.read()
        return None
    else:
        return gen.generate_image(prompt)


if __name__ == "__main__":
    # Test usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python image_generator.py <prompt> [output.png]")
        print("Example: python image_generator.py 'a cat in space' cat.png")
        sys.exit(1)
    
    prompt = sys.argv[1]
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    
    logging.basicConfig(level=logging.INFO)
    
    if output:
        generate_image_simple(prompt, output)
    else:
        img_bytes = generate_image_simple(prompt)
        if img_bytes:
            print(f"✅ Generated {len(img_bytes)} bytes")
        else:
            print("❌ Generation failed")
