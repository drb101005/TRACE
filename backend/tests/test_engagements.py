"""Test engagement management and authorization."""
import pytest
from datetime import datetime
from app.domain.enums import UserRole


def test_client_create_engagement(client, auth_headers):
    """Test that client employee can create engagement."""
    response = client.post(
        "/api/v1/engagements/",
        headers=auth_headers[UserRole.CLIENT_EMPLOYEE],
        json={
            "name": "Test Audit 2024",
            "client_name": "Test Company Ltd",
            "reporting_period_start": "2023-04-01T00:00:00",
            "reporting_period_end": "2024-03-31T23:59:59",
            "description": "Test engagement"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Audit 2024"
    assert data["status"] == "draft"


def test_ai_auditor_cannot_create_engagement(client, auth_headers):
    """Test that AI auditor cannot create engagement."""
    response = client.post(
        "/api/v1/engagements/",
        headers=auth_headers[UserRole.INDEPENDENT_AI_AUDITOR],
        json={
            "name": "Test Audit",
            "client_name": "Test Company",
            "reporting_period_start": "2023-04-01T00:00:00",
            "reporting_period_end": "2024-03-31T23:59:59"
        }
    )
    
    assert response.status_code == 403


def test_human_auditor_cannot_create_engagement(client, auth_headers):
    """Test that human auditor cannot create engagement."""
    response = client.post(
        "/api/v1/engagements/",
        headers=auth_headers[UserRole.HUMAN_AUDITOR],
        json={
            "name": "Test Audit",
            "client_name": "Test Company",
            "reporting_period_start": "2023-04-01T00:00:00",
            "reporting_period_end": "2024-03-31T23:59:59"
        }
    )
    
    assert response.status_code == 403


def test_admin_create_engagement(client, auth_headers):
    """Test that platform admin can create engagement."""
    response = client.post(
        "/api/v1/engagements/",
        headers=auth_headers[UserRole.PLATFORM_ADMIN],
        json={
            "name": "Admin Created Audit",
            "client_name": "Test Company",
            "reporting_period_start": "2023-04-01T00:00:00",
            "reporting_period_end": "2024-03-31T23:59:59"
        }
    )
    
    assert response.status_code == 201


def test_list_engagements_access_control(client, auth_headers, db_session):
    """Test that users see only their accessible engagements."""
    from app.db import models
    from app.domain.enums import UserRole
    
    # Create engagement as client
    response = client.post(
        "/api/v1/engagements/",
        headers=auth_headers[UserRole.CLIENT_EMPLOYEE],
        json={
            "name": "Client Engagement",
            "client_name": "Test Co",
            "reporting_period_start": "2023-04-01T00:00:00",
            "reporting_period_end": "2024-03-31T23:59:59"
        }
    )
    assert response.status_code == 201
    
    # Client sees their engagement
    response = client.get(
        "/api/v1/engagements/",
        headers=auth_headers[UserRole.CLIENT_EMPLOYEE]
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    
    # Auditors see all engagements
    response = client.get(
        "/api/v1/engagements/",
        headers=auth_headers[UserRole.HUMAN_AUDITOR]
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_engagement_by_id(client, auth_headers):
    """Test getting a specific engagement."""
    # Create engagement
    create_response = client.post(
        "/api/v1/engagements/",
        headers=auth_headers[UserRole.CLIENT_EMPLOYEE],
        json={
            "name": "Specific Audit",
            "client_name": "Test Company",
            "reporting_period_start": "2023-04-01T00:00:00",
            "reporting_period_end": "2024-03-31T23:59:59"
        }
    )
    engagement_id = create_response.json()["id"]
    
    # Get engagement
    response = client.get(
        f"/api/v1/engagements/{engagement_id}",
        headers=auth_headers[UserRole.CLIENT_EMPLOYEE]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == engagement_id
    assert data["name"] == "Specific Audit"


def test_update_engagement(client, auth_headers):
    """Test updating engagement details."""
    # Create engagement
    create_response = client.post(
        "/api/v1/engagements/",
        headers=auth_headers[UserRole.CLIENT_EMPLOYEE],
        json={
            "name": "Original Name",
            "client_name": "Test Company",
            "reporting_period_start": "2023-04-01T00:00:00",
            "reporting_period_end": "2024-03-31T23:59:59"
        }
    )
    engagement_id = create_response.json()["id"]
    
    # Update engagement
    response = client.patch(
        f"/api/v1/engagements/{engagement_id}",
        headers=auth_headers[UserRole.CLIENT_EMPLOYEE],
        json={"name": "Updated Name"}
    )
    
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"
