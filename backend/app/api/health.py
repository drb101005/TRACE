"""Health check endpoint."""
from datetime import datetime
from fastapi import APIRouter
from app.domain.schemas import HealthResponse
from app.core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check application health and dependency availability."""
    # Check LLM availability
    llm_available = False
    if settings.llm_enabled and settings.gemini_api_key:
        llm_available = True
    
    # Check OCR availability
    ocr_available = False
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        ocr_available = True
    except Exception:
        pass
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="0.1.0",
        llm_available=llm_available,
        ocr_available=ocr_available
    )
