# app/services/ocr_service.py
import cv2
import numpy as np
import pytesseract
from typing import Tuple, List
import logging
import re

logger = logging.getLogger(__name__)

# Lazy EasyOCR initialization to avoid heavy import failures at module import time
_easy_reader = None
def _get_easy_reader():
    global _easy_reader
    if _easy_reader is None:
        try:
            import easyocr
            _easy_reader = easyocr.Reader(['en'], gpu=False)
            logger.info("EasyOCR initialized")
        except Exception as e:
            logger.warning(f"EasyOCR not available: {e}")
            _easy_reader = None
    return _easy_reader

def _ensure_tesseract_available():
    try:
        # This will raise if tesseract is not available
        ver = pytesseract.get_tesseract_version()
        logger.debug(f"Tesseract version: {ver}")
        return True
    except Exception as e:
        logger.error(f"Tesseract not available or not on PATH: {e}")
        return False

def preprocess(img_b: bytes) -> np.ndarray:
    """
    Preprocess image bytes for better OCR results.
    Denoise, grayscale, threshold and deskew (correctly using text pixels).
    Returns the final binary image (uint8).
    """
    try:
        arr = np.frombuffer(img_b, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Invalid image bytes - could not decode image")

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Denoise - mild blur
        gray = cv2.bilateralFilter(gray, 9, 75, 75)

        # Adaptive thresholding (keeps text as black on white)
        th = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 35, 15
        )

        # Invert if text appears white on black (we want text as black/0)
        # Count black vs white pixels to decide
        white_count = np.sum(th == 255)
        black_count = np.sum(th == 0)
        if white_count < black_count:
            th = cv2.bitwise_not(th)

        # Deskew: find coordinates of text (non-zero -> text if we inverted so text=0),
        # but safer to find non-white pixels
        coords = np.column_stack(np.where(th < 255))
        angle = 0.0
        if coords.size > 0:
            rect = cv2.minAreaRect(coords)
            angle = rect[-1]
            # rect[-1] returns angle in [-90, 0); convert to deskew angle
            if angle < -45:
                angle = 90 + angle
            # we want to rotate by negative of found angle to deskew
            # small angles under ~0.5 deg are ignored
            angle = -angle

        if abs(angle) > 0.5:
            (h, w) = th.shape
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            deskew = cv2.warpAffine(th, M, (w, h),
                                    flags=cv2.INTER_CUBIC,
                                    borderMode=cv2.BORDER_REPLICATE)
            # Recompute thresholding after warp if necessary
            _, deskew = cv2.threshold(deskew, 128, 255, cv2.THRESH_BINARY)
        else:
            deskew = th

        return deskew

    except Exception as e:
        logger.error(f"Error in image preprocessing: {e}")
        raise ValueError(f"Failed to preprocess image: {e}")

def clean_ocr_text(text: str) -> str:
    """
    Clean up OCR extracted text by removing artifacts and fixing common issues.
    Avoid destructive global replacements like 0->O.
    """
    if not text:
        return ""

    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Fix common artifacts conservatively
    text = text.replace('|', 'I')  # pipe often misread in OCR
    # Do NOT replace numeric '0' with letter 'O' globally — that corrupts numbers.

    return text

def ocr_bytes(img_b: bytes) -> Tuple[str, List[dict]]:
    """
    Extract text from image bytes using OCR. Uses Tesseract primarily, falls back to EasyOCR.
    Uses original color image for EasyOCR (better results) and logs raw EasyOCR result.
    """
    try:
        # Decode original color image (for EasyOCR/debugging)
        arr = np.frombuffer(img_b, np.uint8)
        orig_img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if orig_img is None:
            logger.error("Failed to decode original color image for OCR")
        else:
            logger.debug(f"Original image shape: {orig_img.shape}, dtype: {orig_img.dtype}")

        # Preprocess for Tesseract (returns binary/deskewed image)
        processed_img = preprocess(img_b)

        # Debug: optionally save images to /tmp for inspection (comment out in prod)
        try:
            import time, os
            ts = int(time.time() * 1000)
            dbg_dir = "/tmp/ocr_debug"
            os.makedirs(dbg_dir, exist_ok=True)
            if orig_img is not None:
                cv2.imwrite(os.path.join(dbg_dir, f"orig_{ts}.png"), orig_img)
            cv2.imwrite(os.path.join(dbg_dir, f"proc_{ts}.png"), processed_img)
            logger.info(f"Saved debug images to {dbg_dir} (orig_{ts}.png, proc_{ts}.png)")
        except Exception as e:
            logger.debug(f"Failed to save debug images: {e}")

        # Try Tesseract first
        text = ""
        try:
            if _ensure_tesseract_available():
                tesseract_config = "--psm 6"
                text = pytesseract.image_to_string(processed_img, lang="eng", config=tesseract_config).strip()
            else:
                logger.warning("Tesseract not available; skipping Tesseract")
        except Exception as e:
            logger.warning(f"Tesseract OCR exception: {e}")
            text = ""

        # Fallback to EasyOCR when Tesseract output is empty or small
        if (not text or len(text) < 8):
            easy = _get_easy_reader()
            if easy:
                try:
                    logger.info("Using EasyOCR fallback")
                    # Use original color image (or grayscale), not the binary thresholded image
                    easy_img = orig_img if orig_img is not None else processed_img
                    # Raw result - log it for debugging (don't filter yet)
                    raw_result = easy.readtext(easy_img, detail=1)  # detail=1 returns (bbox, text, prob)
                    logger.debug(f"EasyOCR raw result: {raw_result}")

                    # If you want to filter by confidence, do it conservatively
                    texts = []
                    for r in raw_result:
                        # r is typically (bbox, text, prob)
                        try:
                            btext = r[1] if len(r) > 1 else ""
                            conf = float(r[2]) if len(r) > 2 else 0.0
                        except Exception:
                            btext = str(r)
                            conf = 0.0
                        # keep even low-confidence results for initial debugging; later raise threshold
                        if btext and btext.strip():
                            texts.append((btext.strip(), conf))

                    # Log detections
                    logger.info(f"EasyOCR detections count: {len(texts)}")
                    for t, c in texts:
                        logger.debug(f"EasyOCR detection -> text: '{t}' conf: {c}")

                    # Build text string, optionally filter by conf >= 0.2 (tunable)
                    MIN_CONF = 0.2
                    chosen = [t for t, c in texts if c >= MIN_CONF] or [t for t, c in texts]
                    text = " ".join(chosen).strip()
                    logger.info(f"EasyOCR extracted {len(text)} chars after filtering")
                except Exception as e:
                    logger.warning(f"EasyOCR fallback failed: {e}")
            else:
                logger.info("EasyOCR not available")
        
        text = clean_ocr_text(text)
        tables = []
        logger.info(f"OCR completed. Extracted {len(text)} characters")
        return text, tables

    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        return "", []


def ocr_bytes_alternative(img_b: bytes) -> Tuple[str, List[dict]]:
    """
    Alternative OCR path with CLAHE and multiple psm tries for certain images.
    """
    try:
        arr = np.frombuffer(img_b, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Invalid image bytes")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)

        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Ensure text is black (0)
        white_count = np.sum(binary == 255)
        black_count = np.sum(binary == 0)
        if white_count < black_count:
            binary = cv2.bitwise_not(binary)

        configs = ["--psm 6", "--psm 7", "--psm 8"]
        best_text = ""
        for cfg in configs:
            try:
                t = pytesseract.image_to_string(binary, lang="eng", config=cfg).strip()
                if len(t) > len(best_text):
                    best_text = t
            except Exception:
                continue

        return clean_ocr_text(best_text), []

    except Exception as e:
        logger.error(f"Alternative OCR failed: {e}")
        return "", []
