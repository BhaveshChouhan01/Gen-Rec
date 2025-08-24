import os
import tempfile
import time
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

import torch

# Configure model/cache paths via environment variables
HF_HOME = os.getenv("HF_HOME", "./models/huggingface")
TORCH_HOME = os.getenv("TORCH_HOME", "./models/torch")
EASYOCR_MODULE_PATH = os.getenv("EASYOCR_MODULE_PATH", "./models/easyocr")

os.environ["HF_HOME"] = HF_HOME
os.environ["TORCH_HOME"] = TORCH_HOME
os.environ["EASYOCR_MODULE_PATH"] = EASYOCR_MODULE_PATH

logger = logging.getLogger(__name__)

try:
    from diffusers import StableDiffusionPipeline
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False

# Global pipeline
_pipe: Optional[StableDiffusionPipeline] = None
_pipe_lock = torch.multiprocessing.Lock()  # thread-safe lock


def ensure_pipe(model_id: str = "runwayml/stable-diffusion-v1-5", use_gpu: Optional[bool] = None):
    """Lazy load the Stable Diffusion pipeline safely."""
    global _pipe
    if not DIFFUSERS_AVAILABLE:
        raise ImportError("diffusers library not installed. pip install diffusers transformers accelerate")

    if _pipe is not None:
        return

    with _pipe_lock:
        if _pipe is not None:  # double-check inside lock
            return
        logger.info(f"Loading Stable Diffusion model: {model_id}")

        if use_gpu is None:
            use_gpu = torch.cuda.is_available()
        device = "cuda" if use_gpu else "cpu"
        torch_dtype = torch.float16 if use_gpu else torch.float32

        try:
            _pipe = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=torch_dtype,
                safety_checker=None,
                requires_safety_checker=False
            ).to(device)

            if use_gpu:
                try:
                    _pipe.enable_attention_slicing()
                    _pipe.enable_memory_efficient_attention()
                    logger.info("Enabled GPU memory optimizations")
                except Exception as e:
                    logger.warning(f"Memory optimizations failed: {e}")
            logger.info("Pipeline loaded successfully")
        except Exception as e:
            logger.error(f"Pipeline loading failed: {e}")
            raise RuntimeError(f"Pipeline loading failed: {e}")


def generate_image(
    prompt: str,
    output_path: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    num_inference_steps: int = 20,
    guidance_scale: float = 7.5,
    width: int = 512,
    height: int = 512,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """Generate a single image from a prompt."""
    global _pipe

    if not prompt or not prompt.strip():
        return {"success": False, "error": "Prompt cannot be empty"}

    width = (width // 8) * 8
    height = (height // 8) * 8

    if output_path is None:
        temp_dir = Path(tempfile.gettempdir()) / "generated_images"
        temp_dir.mkdir(parents=True, exist_ok=True)
        output_path = temp_dir / f"image_{int(time.time())}.png"
    else:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        ensure_pipe()

        generator = None
        if seed is not None:
            generator = torch.Generator(device=_pipe.device)
            generator.manual_seed(seed)

        start_time = time.time()
        with torch.no_grad():
            result = _pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,
                generator=generator
            )
        generation_time = time.time() - start_time

        image = result.images[0]
        image.save(output_path)

        return {
            "success": True,
            "image_path": str(output_path),
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "parameters": {
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "width": width,
                "height": height,
                "seed": seed
            },
            "generation_time": round(generation_time, 2),
            "file_size": os.path.getsize(output_path)
        }
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return {"success": False, "error": str(e), "prompt": prompt}


def generate_multiple_images(prompts: List[str], output_dir: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
    if output_dir is None:
        output_dir = Path(tempfile.gettempdir()) / "generated_images"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    results = []
    for i, prompt in enumerate(prompts):
        path = Path(output_dir) / f"image_{i:03d}.png"
        results.append(generate_image(prompt, str(path), **kwargs))
    return results


def clear_pipeline():
    global _pipe
    if _pipe is not None:
        logger.info("Clearing pipeline from memory")
        del _pipe
        _pipe = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


# Presets
DEFAULT_NEGATIVE_PROMPT = "blurry, bad anatomy, bad hands, text, error, missing fingers, extra digit, cropped, low quality, watermark"

IMAGE_PRESETS = {
    "photorealistic": {"negative_prompt": DEFAULT_NEGATIVE_PROMPT, "guidance_scale": 7.5, "num_inference_steps": 30},
    "artistic": {"negative_prompt": "blurry, low quality", "guidance_scale": 10.0, "num_inference_steps": 25},
    "fast": {"negative_prompt": DEFAULT_NEGATIVE_PROMPT, "guidance_scale": 7.5, "num_inference_steps": 15}
}


def generate_with_preset(prompt: str, preset: str = "photorealistic", output_path: Optional[str] = None, **override_params):
    if preset not in IMAGE_PRESETS:
        raise ValueError(f"Unknown preset: {preset}. Available: {list(IMAGE_PRESETS.keys())}")
    params = IMAGE_PRESETS[preset].copy()
    params.update(override_params)
    return generate_image(prompt, output_path, **params)
