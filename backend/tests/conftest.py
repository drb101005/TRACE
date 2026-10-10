"""Pytest configuration and fixtures."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.database import Base, get_db
from app.core.security import get_password_hash
from app.db import models
from app.domain.enums import UserRole
from main import app


# Test database
TEST_DATABASE_URL = "sqlite:///./test_trace.db"


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_users(db_session):
    """Create test users for all roles."""
    users = {}
    
    for role in UserRole:
        user = models.User(
            username=f"test_{role.value.lower()}",
            email=f"test_{role.value.lower()}@example.com",
            hashed_password=get_password_hash("testpass123"),
            role=role,
            full_name=f"Test {role.value}"
        )
        db_session.add(user)
        users[role] = user
    
    db_session.commit()
    
    for user in users.values():
        db_session.refresh(user)
    
    return users


@pytest.fixture
def auth_headers(client, test_users):
    """Get authentication headers for different roles."""
    headers = {}
    
    for role, user in test_users.items():
        response = client.post(
            "/api/v1/auth/login",
            json={"username": user.username, "password": "testpass123"}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        headers[role] = {"Authorization": f"Bearer {token}"}
    
    return headers
