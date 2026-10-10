"""Test audit log and hash chain integrity."""
import pytest
from app.services.audit_log import AuditLogService
from app.domain.enums import UserRole, AuditEventAction
from app.db import models


def test_create_audit_event(db_session, test_users):
    """Test creating an audit event."""
    audit_log = AuditLogService(db_session)
    user = test_users[UserRole.CLIENT_EMPLOYEE]
    
    event = audit_log.log_event(
        actor_id=user.id,
        actor_role=user.role,
        action=AuditEventAction.CREATE,
        target_type="Engagement",
        target_id="test-engagement-id",
        engagement_id="test-engagement-id"
    )
    
    assert event.id is not None
    assert event.actor_id == user.id
    assert event.action == AuditEventAction.CREATE
    assert event.event_hash is not None


def test_hash_chain_linkage(db_session, test_users):
    """Test that events are properly linked in hash chain."""
    audit_log = AuditLogService(db_session)
    user = test_users[UserRole.CLIENT_EMPLOYEE]
    
    # Create first event
    event1 = audit_log.log_event(
        actor_id=user.id,
        actor_role=user.role,
        action=AuditEventAction.CREATE,
        target_type="Test",
        target_id="1"
    )
    
    # Create second event
    event2 = audit_log.log_event(
        actor_id=user.id,
        actor_role=user.role,
        action=AuditEventAction.UPDATE,
        target_type="Test",
        target_id="2"
    )
    
    # Verify chain linkage
    assert event1.previous_event_hash is None  # First event
    assert event2.previous_event_hash == event1.event_hash  # Linked


def test_verify_chain_integrity_valid(db_session, test_users):
    """Test verification of valid hash chain."""
    audit_log = AuditLogService(db_session)
    user = test_users[UserRole.CLIENT_EMPLOYEE]
    
    # Create several events
    for i in range(5):
        audit_log.log_event(
            actor_id=user.id,
            actor_role=user.role,
            action=AuditEventAction.CREATE,
            target_type="Test",
            target_id=str(i)
        )
    
    # Verify chain
    result = audit_log.verify_chain_integrity()
    
    assert result["valid"] is True
    assert result["total_events"] == 5
    assert len(result["broken_links"]) == 0
    assert len(result["invalid_hashes"]) == 0


def test_verify_chain_detects_tampering(db_session, test_users):
    """Test that chain verification detects tampering."""
    audit_log = AuditLogService(db_session)
    user = test_users[UserRole.CLIENT_EMPLOYEE]
    
    # Create events
    event1 = audit_log.log_event(
        actor_id=user.id,
        actor_role=user.role,
        action=AuditEventAction.CREATE,
        target_type="Test",
        target_id="1"
    )
    
    event2 = audit_log.log_event(
        actor_id=user.id,
        actor_role=user.role,
        action=AuditEventAction.UPDATE,
        target_type="Test",
        target_id="2"
    )
    
    # Tamper with event2's action (simulating database manipulation)
    event2.action = AuditEventAction.DELETE
    db_session.commit()
    
    # Verify chain - should detect invalid hash
    result = audit_log.verify_chain_integrity()
    
    assert result["valid"] is False
    assert len(result["invalid_hashes"]) > 0


def test_data_fingerprint_calculation(db_session):
    """Test data fingerprint calculation."""
    audit_log = AuditLogService(db_session)
    
    # Test with dict
    data1 = {"key": "value", "number": 123}
    fingerprint1 = audit_log.calculate_data_fingerprint(data1)
    
    # Same data should produce same fingerprint
    data2 = {"number": 123, "key": "value"}  # Different order
    fingerprint2 = audit_log.calculate_data_fingerprint(data2)
    
    assert fingerprint1 == fingerprint2
    
    # Different data should produce different fingerprint
    data3 = {"key": "different", "number": 123}
    fingerprint3 = audit_log.calculate_data_fingerprint(data3)
    
    assert fingerprint1 != fingerprint3
