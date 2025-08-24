# app/services/image_search.py
import aiohttp
import asyncio
import logging
from typing import List, Dict, Optional
from urllib.parse import quote_plus, unquote
from app.core.config import get_settings
from app.models.schemas import ImageProvider

logger = logging.getLogger(__name__)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ImageSearchMVP/1.0; +http://localhost)"
}


async def unsplash_search(session: aiohttp.ClientSession, q: str, limit: int) -> List[Dict]:
    """Search Unsplash images using API key."""
    settings = get_settings()
    api_key = settings.UNSPLASH_ACCESS_KEY
    if not api_key:
        logger.warning("Unsplash API key not set. Skipping Unsplash search.")
        return []

    url = f"https://api.unsplash.com/search/photos?query={quote_plus(q)}&per_page={limit}"

    try:
        async with session.get(url, headers={"Authorization": f"Client-ID {api_key}"}) as resp:
            if resp.status != 200:
                logger.error(f"Unsplash API returned status {resp.status}")
                return []
            data = await resp.json()
    except Exception as e:
        logger.exception(f"Unsplash API error: {e}")
        return []

    results = []
    for item in data.get("results", []):
        try:
            results.append({
                "url": item["urls"]["full"],
                "thumbnail": item["urls"]["small"],
                "provider": ImageProvider.UNSPLASH.value,
                "title": item.get("description") or item.get("alt_description"),
                "license": "unsplash-license",
                "source_page": item["links"]["html"],
                "width": item.get("width"),
                "height": item.get("height"),
            })
        except KeyError as e:
            logger.warning(f"Skipping Unsplash item due to missing field: {e}")
            continue

    return results


async def duckduckgo_search(session: aiohttp.ClientSession, q: str, limit: int) -> List[Dict]:
    """Scrape DuckDuckGo image results (free fallback)."""
    url = f"https://duckduckgo.com/?q={quote_plus(q)}&t=h_&iar=images&iax=images&ia=images"
    ddg_img_re = r'imgurl=(.*?)&'

    try:
        async with session.get(url, headers=HEADERS) as resp:
            if resp.status != 200:
                logger.error(f"DuckDuckGo returned status {resp.status}")
                return []
            html = await resp.text()
    except Exception as e:
        logger.exception(f"DuckDuckGo scraping error: {e}")
        return []

    import re
    candidates = re.findall(ddg_img_re, html, re.IGNORECASE)
    items = []
    seen = set()

    for c in candidates:
        try:
            c = unquote(c)
            if not c.startswith("http") or c in seen:
                continue
            seen.add(c)
            items.append({
                "url": c,
                "thumbnail": c,
                "provider": ImageProvider.DUCKDUCKGO.value,
                "title": None,
                "license": "unknown",
                "source_page": None,
                "width": None,
                "height": None,
            })
            if len(items) >= limit:
                break
        except Exception as e:
            logger.warning(f"Skipping DuckDuckGo URL due to error: {e}")
            continue

    return items


async def search_images(q: str, limit: int = 10, license_filter: Optional[str] = None) -> List[Dict]:
    """Main image search function using multiple providers."""
    if limit <= 0:
        return []

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        results = await unsplash_search(session, q, limit)

        # If Unsplash fails or returns fewer images, try DuckDuckGo
        if len(results) < limit:
            ddg_results = await duckduckgo_search(session, q, limit)
            results.extend(ddg_results)

    # Deduplicate URLs
    seen_urls = set()
    deduped = []
    for r in results:
        if r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            deduped.append(r)

    # Apply license filter if provided
    if license_filter:
        deduped = [r for r in deduped if (r.get("license") or "").startswith(license_filter)]

    return deduped[:limit]
