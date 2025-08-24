from typing import Optional, Tuple
import io
import aiohttp
import asyncio
import logging
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration, pipeline
import torch
from app.core.config import get_settings
from fastapi import APIRouter

router = APIRouter()

# Set up logging
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Lazy singletons for model loading
blip_processor = None
blip_model = None
qa_pipeline = None

def ensure_models():
    """
    Lazy load models to avoid loading them at import time.
    This helps with startup time and memory usage.
    """
    global blip_processor, blip_model, qa_pipeline
    
    try:
        # Load BLIP models for image captioning
        if blip_processor is None or blip_model is None:
            logger.info(f"Loading BLIP model: {settings.blip_model}")
            blip_processor = BlipProcessor.from_pretrained(settings.blip_model)
            blip_model = BlipForConditionalGeneration.from_pretrained(settings.blip_model)
            logger.info("BLIP models loaded successfully")
        
        # Load QA pipeline for question answering
        if qa_pipeline is None:
            logger.info(f"Loading QA model: {settings.qa_model}")
            qa_pipeline = pipeline("question-answering", model=settings.qa_model)
            logger.info("QA pipeline loaded successfully")
            
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise RuntimeError(f"Model loading failed: {e}")

async def fetch_image_bytes(url: str, timeout: int = 30) -> bytes:
    """
    Fetch image bytes from a URL with proper error handling.
    """
    try:
        timeout_config = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=timeout_config) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if not content_type.startswith('image/'):
                    raise ValueError(f"URL does not point to an image. Content-Type: {content_type}")
                
                # Check content length (limit to 10MB)
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > 10 * 1024 * 1024:
                    raise ValueError("Image too large (>10MB)")
                
                return await response.read()
                
    except aiohttp.ClientError as e:
        logger.error(f"HTTP error fetching image from {url}: {e}")
        raise ValueError(f"Failed to fetch image: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching image from {url}: {e}")
        raise ValueError(f"Failed to fetch image: {e}")

async def caption_from_url(image_url: str) -> str:
    """
    Generate a caption for an image from URL using BLIP model.
    """
    try:
        # Ensure models are loaded
        ensure_models()
        
        # Fetch image bytes
        image_bytes = await fetch_image_bytes(image_url)
        
        # Open and convert image
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise ValueError(f"Invalid image format: {e}")
        
        # Generate caption
        inputs = blip_processor(images=image, return_tensors="pt")
        
        with torch.no_grad():
            generated_ids = blip_model.generate(
                **inputs, 
                max_new_tokens=30,
                num_beams=3,
                early_stopping=True
            )
        
        caption = blip_processor.decode(generated_ids[0], skip_special_tokens=True)
        
        # Clean up caption
        caption = caption.strip()
        if not caption:
            caption = "Unable to generate caption for this image."
        
        logger.info(f"Generated caption: {caption[:50]}...")
        return caption
        
    except Exception as e:
        logger.error(f"Caption generation failed: {e}")
        return f"Failed to generate caption: {str(e)}"

def answer_from_context(question: str, context: str, max_answer_len: int = 100) -> Tuple[str, Optional[float]]:
    """
    Answer a question based on provided context using QA pipeline.
    """
    try:
        # Ensure models are loaded
        ensure_models()
        
        # Validate inputs
        if not question.strip():
            return "Please provide a valid question.", None
        
        if not context.strip():
            return "I don't have enough information in the image text/caption to answer this question.", None
        
        # Truncate context if too long (BERT models have token limits)
        if len(context) > 2000:  # Rough character limit
            context = context[:2000] + "..."
            logger.warning("Context truncated due to length")
        
        # Get answer from QA pipeline
        result = qa_pipeline(
            question=question.strip(), 
            context=context.strip(),
            max_answer_len=max_answer_len
        )
        
        answer = result.get("answer", "").strip()
        confidence = result.get("score")
        
        # Convert confidence to float if it exists
        if confidence is not None:
            confidence = float(confidence)
            
        # Handle empty answers
        if not answer:
            answer = "I couldn't find a specific answer to your question in the provided context."
            confidence = 0.0
        
        # Log low confidence answers
        if confidence is not None and confidence < 0.3:
            logger.warning(f"Low confidence answer: {confidence:.2f}")
        
        return answer, confidence
        
    except Exception as e:
        logger.error(f"QA processing failed: {e}")
        return f"Failed to process question: {str(e)}", None

async def caption_from_bytes(image_bytes: bytes) -> str:
    """
    Generate caption from image bytes (useful for uploaded files).
    """
    try:
        ensure_models()
        
        # Open and convert image
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise ValueError(f"Invalid image format: {e}")
        
        # Generate caption
        inputs = blip_processor(images=image, return_tensors="pt")
        
        with torch.no_grad():
            generated_ids = blip_model.generate(
                **inputs, 
                max_new_tokens=30,
                num_beams=3,
                early_stopping=True
            )
        
        caption = blip_processor.decode(generated_ids[0], skip_special_tokens=True)
        caption = caption.strip()
        
        if not caption:
            caption = "Unable to generate caption for this image."
        
        return caption
        
    except Exception as e:
        logger.error(f"Caption generation from bytes failed: {e}")
        return f"Failed to generate caption: {str(e)}"

def get_model_info() -> dict:
    """
    Get information about loaded models.
    """
    return {
        "blip_model": settings.blip_model if hasattr(settings, 'blip_model') else "Not configured",
        "qa_model": settings.qa_model if hasattr(settings, 'qa_model') else "Not configured",
        "models_loaded": {
            "blip_processor": blip_processor is not None,
            "blip_model": blip_model is not None,
            "qa_pipeline": qa_pipeline is not None
        }
    }