"""Authentication and authorization utilities."""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    """Get the current authenticated user from JWT token."""
    payload = decode_token(credentials.credentials)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


def require_role(allowed_roles: list[str]):
    """Dependency factory to require specific roles."""
    async def role_checker(current_user: models.User = Depends(get_current_user)) -> models.User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


def check_engagement_access(
    user: models.User,
    engagement_id: str,
    db: Session
) -> bool:
    """Check if user has access to a specific engagement."""
    # Platform admin has access to all engagements
    if user.role == "PLATFORM_ADMIN":
        return True
    
    # Check if engagement exists
    engagement = db.query(models.Engagement).filter(
        models.Engagement.id == engagement_id
    ).first()
    
    if not engagement:
        return False
    
    # Client employees can only access their own engagements
    if user.role == "CLIENT_EMPLOYEE":
        return engagement.client_user_id == user.id
    
    # Auditors can access all engagements (read-only enforced elsewhere)
    if user.role in ["INDEPENDENT_AI_AUDITOR", "HUMAN_AUDITOR"]:
        return True
    
    return False
