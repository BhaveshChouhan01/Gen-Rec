# app/api/routes/search.py
from fastapi import APIRouter
from typing import List
from app.services.image_search import search_images
from app.models.schemas import SearchRequest, SearchResponse, ImageItem

router = APIRouter(prefix="/api", tags=["search"])

@router.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    """
    Search images from multiple providers (Unsplash, DuckDuckGo).
    """
    results = await search_images(
        q=request.q,
        limit=request.limit,
        license_filter=request.license
    )

    items: List[ImageItem] = [ImageItem(**r) for r in results]

    return SearchResponse(
        results=items,
        total=len(items),
        total_pages=1,
        current_page=1
    )