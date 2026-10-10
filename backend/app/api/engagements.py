"""Engagement management endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.domain.schemas import (
    EngagementCreate,
    EngagementUpdate,
    EngagementResponse
)
from app.core.security import get_current_user, check_engagement_access
from app.core.errors import raise_403, raise_404

router = APIRouter()


@router.post("/", response_model=EngagementResponse, status_code=status.HTTP_201_CREATED)
async def create_engagement(
    engagement_data: EngagementCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new audit engagement."""
    # Only client employees and admins can create engagements
    if current_user.role not in ["CLIENT_EMPLOYEE", "PLATFORM_ADMIN"]:
        raise_403("Only clients and administrators can create engagements")
    
    engagement = models.Engagement(
        name=engagement_data.name,
        client_name=engagement_data.client_name,
        client_user_id=current_user.id if current_user.role == "CLIENT_EMPLOYEE" else None,
        reporting_period_start=engagement_data.reporting_period_start,
        reporting_period_end=engagement_data.reporting_period_end,
        description=engagement_data.description
    )
    
    db.add(engagement)
    db.commit()
    db.refresh(engagement)
    
    return engagement


@router.get("/", response_model=List[EngagementResponse])
async def list_engagements(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all engagements accessible to the current user."""
    query = db.query(models.Engagement)
    
    # Filter by user role
    if current_user.role == "CLIENT_EMPLOYEE":
        # Client can only see their own engagements
        query = query.filter(models.Engagement.client_user_id == current_user.id)
    # Auditors and admins can see all engagements
    
    engagements = query.order_by(models.Engagement.created_at.desc()).all()
    return engagements


@router.get("/{engagement_id}", response_model=EngagementResponse)
async def get_engagement(
    engagement_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific engagement."""
    engagement = db.query(models.Engagement).filter(
        models.Engagement.id == engagement_id
    ).first()
    
    if not engagement:
        raise_404("Engagement not found")
    
    # Check access
    if not check_engagement_access(current_user, engagement_id, db):
        raise_403("Access to this engagement is forbidden")
    
    return engagement


@router.patch("/{engagement_id}", response_model=EngagementResponse)
async def update_engagement(
    engagement_id: str,
    update_data: EngagementUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an engagement."""
    engagement = db.query(models.Engagement).filter(
        models.Engagement.id == engagement_id
    ).first()
    
    if not engagement:
        raise_404("Engagement not found")
    
    # Check access
    if not check_engagement_access(current_user, engagement_id, db):
        raise_403("Access to this engagement is forbidden")
    
    # Only client and admin can update certain fields
    if current_user.role not in ["CLIENT_EMPLOYEE", "PLATFORM_ADMIN"]:
        if update_data.name or update_data.description:
            raise_403("Only clients and administrators can update engagement details")
    
    # Update fields
    if update_data.name is not None:
        engagement.name = update_data.name
    if update_data.description is not None:
        engagement.description = update_data.description
    if update_data.status is not None:
        # Status updates might have workflow restrictions
        engagement.status = update_data.status
    
    db.commit()
    db.refresh(engagement)
    
    return engagement
