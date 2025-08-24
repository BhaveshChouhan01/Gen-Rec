from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from enum import Enum

# Enums
class ImageProvider(str, Enum):
    UNSPLASH = "unsplash"

# Base models for reusability
class BoundingBox(BaseModel):
    coordinates: List[List[float]]

class ImageMetadata(BaseModel):
    width: int
    height: int
    file_size: int
    format: Optional[str] = None
    aspect_ratio: float

class TableData(BaseModel):
    headers: List[str]
    rows: List[List[str]]

class OCRResult(BaseModel):
    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: Optional[BoundingBox] = None

# Search related models
class SearchRequest(BaseModel):
    q: str = Field(..., min_length=1)
    limit: int = 10
    license: Optional[str] = None  # "cc", "unknown", etc.

class ImageItem(BaseModel):
    url: HttpUrl
    thumbnail: Optional[HttpUrl] = None
    provider: str
    title: Optional[str] = None
    license: Optional[str] = None
    source_page: Optional[HttpUrl] = None
    width: Optional[int] = None
    height: Optional[int] = None

class SearchResponse(BaseModel):
    results: List[ImageItem] = []
    total: int = 0
    total_pages: int = 0
    current_page: int = 1

# Analysis related models
class AnalysisRequest(BaseModel):
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    features: Optional[List[str]] = []  # e.g. ["ocr", "tables", "faces"]

class ContentAnalysis(BaseModel):
    type: str
    contains_text: bool
    text_length: int
    likely_content: List[str] = []
    aspect_ratio: float
    confidence_score: Optional[float] = None

class ImageAnalysisResponse(BaseModel):
    ocr_results: List[OCRResult]
    full_text: str
    image_info: ImageMetadata
    analysis: ContentAnalysis
    tables: Optional[List[TableData]] = None
    processing_time: Optional[float] = None

# OCR specific models
class OCRResponse(BaseModel):
    text: str
    tables: List[TableData] = []

# VQA (Visual Question Answering) models
class VQARequest(BaseModel):
    image_url: Optional[str] = None
    question: str
    ocr_text_hint: Optional[str] = None

class VQAResponse(BaseModel):
    caption: str
    answer: str
    confidence: Optional[float] = None
    context_used: str
    sources: List[Dict[str, Any]] = []

# Error and Health models
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    services: Dict[str, str]