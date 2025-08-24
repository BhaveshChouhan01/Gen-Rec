from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any
import os
import asyncio
from app.services.generation_service import generate_image

router = APIRouter(prefix="/api", tags=["generation"])


class GenRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000, description="Image generation prompt")


class GenResponse(BaseModel):
    prompt: str
    image_url: str
    status: str = "success"


@router.post("/generate", response_model=GenResponse)
async def generate(req: GenRequest):
    loop = asyncio.get_event_loop()
    # Run CPU/GPU intensive generation in executor to avoid blocking
    result: Dict[str, Any] = await loop.run_in_executor(None, generate_image, req.prompt)

    if not result.get("success") or not result.get("image_path") or not os.path.exists(result["image_path"]):
        raise HTTPException(status_code=500, detail=result.get("error", "Image generation failed"))

    # Convert absolute path to relative URL
    filename = os.path.basename(result["image_path"])
    image_url = f"/static/images/{filename}"

    return GenResponse(prompt=req.prompt, image_url=image_url)