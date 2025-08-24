from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import tempfile
import shutil
import os
import logging
from app.services.pdf_service import extract_tables_from_pdf, download_csv_files

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["pdf"])

@router.post("/ocr-pdf")
async def ocr_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF, extract tables using Camelot, and return a downloadable ZIP of CSVs.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, detail="Upload a PDF file")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    try:
        # Save uploaded file
        with open(tmp.name, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Extract tables → returns list of dicts with csv_path
        csvs = extract_tables_from_pdf(tmp.name)

        if not csvs:
            raise HTTPException(404, detail="No tables found in the PDF")

        # Bundle extracted CSVs into a ZIP
        zip_path = download_csv_files(csvs)

        logger.info(f"Extracted {len(csvs)} tables, packaged at {zip_path}")

        # Return ZIP file as download response
        return FileResponse(
            path=zip_path,
            filename="extracted_tables.zip",
            media_type="application/zip"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(500, detail=f"Error processing PDF: {str(e)}")
    finally:
        tmp.close()
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)
