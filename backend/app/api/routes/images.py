from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import aiohttp
from app.models.schemas import VQARequest, VQAResponse
from app.services.analysis_service import caption_from_url, answer_from_context
from app.services.ocr_service import ocr_bytes
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from typing import Optional

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])

@router.post("/vqa", response_model=VQAResponse)
async def vqa(req: VQARequest):
    """
    Visual Question Answering endpoint.
    Combines image captioning, OCR, and question answering.
    """
    try:
        # Validate request
        if not req.image_url:
            raise HTTPException(status_code=400, detail="image_url is required")
        
        if not req.question or not req.question.strip():
            raise HTTPException(status_code=400, detail="question is required")
        
        logger.info(f"VQA request for image: {req.image_url}, question: {req.question}")
        
        # 1) Generate caption for the image
        try:
            caption = await caption_from_url(req.image_url)
            logger.info(f"Generated caption: {caption}")
        except Exception as e:
            logger.error(f"Caption generation failed: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to generate caption: {str(e)}")
        
        # 2) Download image and perform OCR
        ocr_text = ""
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(req.image_url) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to fetch image: HTTP {response.status}")
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Unable to fetch image from URL (HTTP {response.status})"
                        )
                    
                    # Check content type
                    content_type = response.headers.get('content-type', '').lower()
                    if not content_type.startswith('image/'):
                        raise HTTPException(
                            status_code=400,
                            detail=f"URL does not point to an image. Content-Type: {content_type}"
                        )
                    
                    img_bytes = await response.read()
                    
            # Perform OCR
            ocr_text, tables = ocr_bytes(img_bytes)  # Fixed syntax error here
            logger.info(f"OCR extracted {len(ocr_text)} characters")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            # Don't fail the entire request if OCR fails
            ocr_text = ""
            logger.warning("Continuing without OCR text due to processing error")
        
        # 3) Build context from multiple sources
        context_parts = []
        
        # Always include caption
        if caption and caption.strip():
            context_parts.append(f"Image description: {caption}")
        
        # Include OCR text if available
        if ocr_text and ocr_text.strip():
            context_parts.append(f"Text visible in image: {ocr_text}")
        
        # Include user hint if provided
        if req.ocr_text_hint and req.ocr_text_hint.strip():
            context_parts.append(f"Additional context: {req.ocr_text_hint}")
        
        # Combine all context
        context = "\n".join(context_parts)
        
        if not context.strip():
            context = "No visual information could be extracted from the image."
        
        logger.info(f"Built context with {len(context)} characters")
        
        # 4) Answer question using the context
        try:
            answer, confidence_score = answer_from_context(req.question, context)
            logger.info(f"Generated answer: {answer}, confidence: {confidence_score}")
        except Exception as e:
            logger.error(f"Question answering failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")
        
        # 5) Build response
        sources = [
            {
                "provider": "image_url",
                "url": req.image_url,
                "type": "image"
            }
        ]
        
        # Add OCR source if text was extracted
        if ocr_text:
            sources.append({
                "provider": "ocr",
                "type": "text_extraction",
                "length": len(ocr_text)
            })
        
        response = VQAResponse(
            caption=caption,
            answer=answer,
            confidence=confidence_score,
            context_used=context,
            sources=sources
        )
        
        logger.info("VQA request completed successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"VQA request failed: {e}")
        raise HTTPException(status_code=500, detail="VQA processing failed")
    
@router.post("/ocr")
async def image_ocr(
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None)
):
    """
    OCR endpoint. Provide either a multipart file upload (field name 'file')
    OR a form field 'image_url'. Returns extracted text and basic metadata.
    """
    try:
        if file is None and (not image_url or not image_url.strip()):
            raise HTTPException(status_code=400, detail="Either 'file' or 'image_url' is required")

        img_bytes = None

        # 1) If file provided, read it
        if file:
            content = await file.read()
            if not content:
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
            img_bytes = content

        # 2) Else fetch from image_url
        elif image_url:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        raise HTTPException(status_code=400, detail=f"Failed to fetch image (HTTP {resp.status})")
                    content_type = resp.headers.get("content-type", "").lower()
                    if not content_type.startswith("image/"):
                        raise HTTPException(status_code=400, detail=f"URL does not point to an image. Content-Type: {content_type}")
                    img_bytes = await resp.read()

        # 3) Run OCR
        text, tables = ocr_bytes(img_bytes)

        return {
            "ok": True,
            "text": text,
            "length": len(text),
            "tables_found": len(tables),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="OCR processing failed")
    
@router.post("/caption")
async def generate_caption(image_url: str):
    """
    Generate caption for an image URL.
    """
    try:
        if not image_url:
            raise HTTPException(status_code=400, detail="image_url is required")
        
        caption = await caption_from_url(image_url)
        
        return {
            "caption": caption,
            "image_url": image_url,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Caption generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Caption generation failed: {str(e)}")

@router.post("/answer")
async def answer_question(question: str, context: str):
    """
    Answer a question given some context text.
    """
    try:
        if not question or not question.strip():
            raise HTTPException(status_code=400, detail="question is required")
        
        if not context or not context.strip():
            raise HTTPException(status_code=400, detail="context is required")
        
        answer, confidence = answer_from_context(question, context)
        
        return {
            "question": question,
            "answer": answer,
            "confidence": confidence,
            "context_length": len(context),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Question answering failed: {e}")
        raise HTTPException(status_code=500, detail=f"Question answering failed: {str(e)}")

@router.get("/health")
async def analysis_health():
    """
    Health check for analysis service.
    """
    try:
        # You could add model loading checks here
        # from app.services.analysis_service import get_model_info
        # model_info = get_model_info()
        
        return {
            "status": "healthy",
            "service": "vqa-analysis",
            # "models": model_info,  # Uncomment when you add get_model_info function
            "endpoints": {
                "vqa": "/api/vqa",
                "caption": "/api/caption", 
                "answer": "/api/answer"
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }