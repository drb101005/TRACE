"""File upload endpoints."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db import models
from app.domain.schemas import UploadResponse, ValidationResult
from app.domain.enums import AuditEventAction
from app.core.security import get_current_user, check_engagement_access
from app.core.errors import raise_403, raise_404, raise_400
from app.core.config import settings
from app.services.ingestion import IngestionService
from app.services.validation import ValidationService
from app.services.audit_log import AuditLogService

router = APIRouter()


@router.post("/{engagement_id}/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    engagement_id: str,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a source file to an engagement."""
    # Check engagement exists and user has access
    engagement = db.query(models.Engagement).filter(
        models.Engagement.id == engagement_id
    ).first()
    
    if not engagement:
        raise_404("Engagement not found")
    
    if not check_engagement_access(current_user, engagement_id, db):
        raise_403("Access to this engagement is forbidden")
    
    # Only clients and admins can upload
    if current_user.role not in ["CLIENT_EMPLOYEE", "PLATFORM_ADMIN"]:
        raise_403("Only client employees and administrators can upload files")
    
    # Read file content
    file_content = await file.read()
    
    # Check size limit
    if len(file_content) > settings.max_upload_size_bytes:
        raise_400(f"File size exceeds maximum allowed ({settings.max_upload_size_mb}MB)")
    
    # Initialize services
    ingestion = IngestionService()
    audit_log = AuditLogService(db)
    
    # Detect file type
    try:
        file_type = ingestion.detect_file_type(file.filename, file.content_type)
    except Exception as e:
        raise_400(str(e))
    
    # Save file
    safe_filename, storage_path, sha256_hash, size_bytes = ingestion.save_file(
        file_content, file.filename, engagement_id
    )
    
    # Create source artifact record
    artifact = models.SourceArtifact(
        engagement_id=engagement_id,
        original_filename=file.filename,
        safe_filename=safe_filename,
        file_type=file_type,
        mime_type=file.content_type,
        size_bytes=size_bytes,
        sha256_hash=sha256_hash,
        storage_path=storage_path,
        uploader_id=current_user.id
    )
    
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    
    # Log audit event
    audit_log.log_event(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action=AuditEventAction.UPLOAD,
        target_type="SourceArtifact",
        target_id=artifact.id,
        engagement_id=engagement_id,
        result_fingerprint=sha256_hash,
        event_data={
            "filename": file.filename,
            "file_type": file_type.value,
            "size_bytes": size_bytes
        }
    )
    
    return artifact


@router.get("/{engagement_id}/uploads", response_model=List[UploadResponse])
async def list_uploads(
    engagement_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all uploaded files for an engagement."""
    # Check access
    if not check_engagement_access(current_user, engagement_id, db):
        raise_403("Access to this engagement is forbidden")
    
    uploads = db.query(models.SourceArtifact).filter(
        models.SourceArtifact.engagement_id == engagement_id
    ).order_by(models.SourceArtifact.upload_timestamp.desc()).all()
    
    return uploads


@router.post("/{engagement_id}/validate/{artifact_id}", response_model=ValidationResult)
async def validate_upload(
    engagement_id: str,
    artifact_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate an uploaded file."""
    # Check access
    if not check_engagement_access(current_user, engagement_id, db):
        raise_403("Access to this engagement is forbidden")
    
    # Get artifact
    artifact = db.query(models.SourceArtifact).filter(
        models.SourceArtifact.id == artifact_id,
        models.SourceArtifact.engagement_id == engagement_id
    ).first()
    
    if not artifact:
        raise_404("Upload not found")
    
    # Get engagement for reporting period
    engagement = db.query(models.Engagement).filter(
        models.Engagement.id == engagement_id
    ).first()
    
    # Initialize services
    ingestion = IngestionService()
    validation = ValidationService()
    
    # Extract data based on file type
    try:
        if artifact.file_type.value == "csv":
            df, metadata = ingestion.extract_csv(artifact.storage_path)
            result = validation.validate_sales_register(
                df, engagement.reporting_period_start, engagement.reporting_period_end
            )
        elif artifact.file_type.value == "xlsx":
            df, metadata = ingestion.extract_xlsx(artifact.storage_path)
            result = validation.validate_sales_register(
                df, engagement.reporting_period_start, engagement.reporting_period_end
            )
        else:
            raise_400(f"Validation not implemented for {artifact.file_type.value} files")
        
        # Create source version with extraction metadata
        source_version = models.SourceVersion(
            artifact_id=artifact.id,
            version_number=1,
            extraction_method=metadata["extraction_method"],
            row_count=metadata.get("row_count"),
            column_count=metadata.get("column_count"),
            metadata_json=metadata
        )
        db.add(source_version)
        db.commit()
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )
