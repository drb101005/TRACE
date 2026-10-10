"""Test authentication and authorization."""
import pytest
from app.domain.enums import UserRole


def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepass123",
            "role": "CLIENT_EMPLOYEE",
            "full_name": "New User"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "CLIENT_EMPLOYEE"
    assert "id" in data


def test_register_duplicate_username(client, test_users):
    """Test that duplicate username is rejected."""
    existing_user = test_users[UserRole.CLIENT_EMPLOYEE]
    
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": existing_user.username,
            "email": "different@example.com",
            "password": "password123",
            "role": "CLIENT_EMPLOYEE"
        }
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login_success(client, test_users):
    """Test successful login."""
    user = test_users[UserRole.CLIENT_EMPLOYEE]
    
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": user.username,
            "password": "testpass123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client, test_users):
    """Test login with wrong password."""
    user = test_users[UserRole.CLIENT_EMPLOYEE]
    
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": user.username,
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401


def test_get_current_user(client, auth_headers):
    """Test getting current user info."""
    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers[UserRole.CLIENT_EMPLOYEE]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "CLIENT_EMPLOYEE"


def test_unauthorized_access(client):
    """Test that unauthorized requests are rejected."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403  # No Bearer token
