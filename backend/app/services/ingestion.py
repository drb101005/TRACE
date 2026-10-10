"""File ingestion and extraction service."""
import os
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
import pandas as pd
import fitz  # PyMuPDF
from PIL import Image
import io

from app.domain.enums import FileType, ExtractionMethod
from app.core.errors import FileProcessingException


class IngestionService:
    """Handle file upload, extraction, and parsing."""
    
    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Check OCR availability
        self.ocr_available = self._check_ocr_available()
    
    def _check_ocr_available(self) -> bool:
        """Check if Tesseract OCR is available."""
        try:
            import pytesseract
            # Try to get tesseract version
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
    
    def save_file(
        self,
        file_content: bytes,
        original_filename: str,
        engagement_id: str
    ) -> Tuple[str, str, str, int]:
        """
        Save uploaded file securely.
        
        Returns: (safe_filename, storage_path, sha256_hash, size_bytes)
        """
        # Calculate SHA-256 hash
        sha256_hash = hashlib.sha256(file_content).hexdigest()
        
        # Generate safe filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_ext = Path(original_filename).suffix.lower()
        safe_filename = f"{engagement_id}_{timestamp}_{sha256_hash[:8]}{file_ext}"
        
        # Create engagement subdirectory
        eng_dir = self.upload_dir / engagement_id
        eng_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        storage_path = eng_dir / safe_filename
        with open(storage_path, "wb") as f:
            f.write(file_content)
        
        size_bytes = len(file_content)
        
        return safe_filename, str(storage_path), sha256_hash, size_bytes
    
    def detect_file_type(self, filename: str, mime_type: Optional[str] = None) -> FileType:
        """Detect file type from filename and MIME type."""
        ext = Path(filename).suffix.lower()
        
        if ext == ".csv":
            return FileType.CSV
        elif ext in [".xlsx", ".xls"]:
            return FileType.XLSX
        elif ext == ".pdf":
            return FileType.PDF
        elif ext in [".jpg", ".jpeg", ".png", ".tiff", ".tif"]:
            return FileType.IMAGE
        
        # Fallback to MIME type
        if mime_type:
            if "csv" in mime_type:
                return FileType.CSV
            elif "spreadsheet" in mime_type or "excel" in mime_type:
                return FileType.XLSX
            elif "pdf" in mime_type:
                return FileType.PDF
            elif "image" in mime_type:
                return FileType.IMAGE
        
        raise FileProcessingException(f"Unsupported file type: {filename}")
    
    def extract_csv(self, file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Extract data from CSV file."""
        try:
            df = pd.read_csv(file_path)
            
            metadata = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
                "extraction_method": ExtractionMethod.PANDAS_CSV
            }
            
            return df, metadata
        except Exception as e:
            raise FileProcessingException(f"Failed to parse CSV: {str(e)}")
    
    def extract_xlsx(self, file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Extract data from XLSX file."""
        try:
            # Read first sheet by default
            df = pd.read_excel(file_path, engine="openpyxl")
            
            # Get sheet names
            with pd.ExcelFile(file_path, engine="openpyxl") as xls:
                sheet_names = xls.sheet_names
            
            metadata = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
                "sheet_names": sheet_names,
                "sheet_name": sheet_names[0] if sheet_names else None,
                "extraction_method": ExtractionMethod.OPENPYXL
            }
            
            return df, metadata
        except Exception as e:
            raise FileProcessingException(f"Failed to parse XLSX: {str(e)}")
    
    def extract_pdf_text(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from PDF using PyMuPDF."""
        try:
            doc = fitz.open(file_path)
            text_content = []
            page_has_text = []
            
            for page_num, page in enumerate(doc):
                text = page.get_text()
                text_content.append(text)
                page_has_text.append(bool(text.strip()))
            
            doc.close()
            
            full_text = "\n\n".join(text_content)
            pages_without_text = [i for i, has_text in enumerate(page_has_text) if not has_text]
            
            metadata = {
                "page_count": len(page_has_text),
                "pages_with_text": sum(page_has_text),
                "pages_without_text": pages_without_text,
                "extraction_method": ExtractionMethod.PYMUPDF_TEXT,
                "text_length": len(full_text)
            }
            
            # If no text extracted, flag for OCR
            if not full_text.strip():
                metadata["requires_ocr"] = True
            
            return full_text, metadata
        except Exception as e:
            raise FileProcessingException(f"Failed to extract PDF text: {str(e)}")
    
    def extract_pdf_with_ocr(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from PDF using OCR on images."""
        if not self.ocr_available:
            raise FileProcessingException(
                "OCR not available. Install Tesseract OCR to process scanned documents."
            )
        
        try:
            import pytesseract
            
            doc = fitz.open(file_path)
            text_content = []
            confidences = []
            
            for page_num, page in enumerate(doc):
                # Convert page to image
                pix = page.get_pixmap(dpi=300)
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                # Perform OCR
                ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                page_text = " ".join([
                    text for text, conf in zip(ocr_data["text"], ocr_data["conf"])
                    if conf > 0
                ])
                
                text_content.append(page_text)
                # Average confidence for page
                valid_confs = [c for c in ocr_data["conf"] if c > 0]
                if valid_confs:
                    confidences.append(sum(valid_confs) / len(valid_confs))
            
            doc.close()
            
            full_text = "\n\n".join(text_content)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            metadata = {
                "page_count": len(text_content),
                "extraction_method": ExtractionMethod.TESSERACT_OCR,
                "text_length": len(full_text),
                "average_confidence": avg_confidence / 100.0,  # Normalize to 0-1
                "ocr_used": True
            }
            
            return full_text, metadata
        except ImportError:
            raise FileProcessingException(
                "pytesseract not installed. Install it to use OCR functionality."
            )
        except Exception as e:
            raise FileProcessingException(f"OCR extraction failed: {str(e)}")
    
    def extract_image_with_ocr(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from image using OCR."""
        if not self.ocr_available:
            raise FileProcessingException(
                "OCR not available. Install Tesseract OCR to process image documents."
            )
        
        try:
            import pytesseract
            
            image = Image.open(file_path)
            
            # Perform OCR
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            text = " ".join([
                t for t, conf in zip(ocr_data["text"], ocr_data["conf"])
                if conf > 0
            ])
            
            # Calculate average confidence
            valid_confs = [c for c in ocr_data["conf"] if c > 0]
            avg_confidence = sum(valid_confs) / len(valid_confs) if valid_confs else 0
            
            metadata = {
                "extraction_method": ExtractionMethod.TESSERACT_OCR,
                "text_length": len(text),
                "average_confidence": avg_confidence / 100.0,
                "ocr_used": True,
                "image_size": image.size
            }
            
            return text, metadata
        except ImportError:
            raise FileProcessingException(
                "pytesseract not installed. Install it to use OCR functionality."
            )
        except Exception as e:
            raise FileProcessingException(f"Image OCR failed: {str(e)}")
