"""Audit event logging with hash chain for tamper-evidence."""
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.db import models
from app.domain.enums import AuditEventAction, UserRole


class AuditLogService:
    """Create and verify append-only hash-linked audit events."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_event(
        self,
        actor_id: str,
        actor_role: UserRole,
        action: AuditEventAction,
        target_type: str,
        target_id: str,
        engagement_id: Optional[str] = None,
        target_version: Optional[int] = None,
        input_fingerprint: Optional[str] = None,
        result_fingerprint: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> models.AuditEvent:
        """
        Log an audit event with hash chain linkage.
        
        Returns the created audit event.
        """
        # Get previous event hash for chain linkage
        previous_event = self.db.query(models.AuditEvent).order_by(
            models.AuditEvent.event_timestamp.desc()
        ).first()
        
        previous_event_hash = previous_event.event_hash if previous_event else None
        
        # Create event
        event = models.AuditEvent(
            event_timestamp=datetime.utcnow(),
            actor_id=actor_id,
            actor_role=actor_role,
            engagement_id=engagement_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_version=target_version,
            input_fingerprint=input_fingerprint,
            result_fingerprint=result_fingerprint,
            previous_event_hash=previous_event_hash,
            correlation_id=correlation_id,
            run_id=run_id,
            event_data=event_data or {}
        )
        
        # Calculate event hash
        event.event_hash = self._calculate_event_hash(event)
        
        # Save to database
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        return event
    
    def _calculate_event_hash(self, event: models.AuditEvent) -> str:
        """Calculate SHA-256 hash of event data."""
        # Create deterministic string representation
        hash_input = {
            "timestamp": event.event_timestamp.isoformat(),
            "actor_id": event.actor_id,
            "actor_role": event.actor_role.value,
            "engagement_id": event.engagement_id,
            "action": event.action.value,
            "target_type": event.target_type,
            "target_id": event.target_id,
            "target_version": event.target_version,
            "input_fingerprint": event.input_fingerprint,
            "result_fingerprint": event.result_fingerprint,
            "previous_event_hash": event.previous_event_hash,
            "event_data": event.event_data
        }
        
        # Convert to JSON with sorted keys for determinism
        hash_str = json.dumps(hash_input, sort_keys=True, default=str)
        
        # Calculate SHA-256
        return hashlib.sha256(hash_str.encode()).hexdigest()
    
    def verify_chain_integrity(
        self,
        engagement_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify the integrity of the audit event hash chain.
        
        Returns verification result with any broken links.
        """
        query = self.db.query(models.AuditEvent).order_by(
            models.AuditEvent.event_timestamp.asc()
        )
        
        if engagement_id:
            query = query.filter(models.AuditEvent.engagement_id == engagement_id)
        
        events = query.all()
        
        if not events:
            return {
                "valid": True,
                "total_events": 0,
                "message": "No events to verify"
            }
        
        broken_links = []
        invalid_hashes = []
        previous_hash = None
        
        for event in events:
            # Check if previous hash matches
            if event.previous_event_hash != previous_hash:
                broken_links.append({
                    "event_id": event.id,
                    "timestamp": event.event_timestamp.isoformat(),
                    "expected_previous": previous_hash,
                    "actual_previous": event.previous_event_hash
                })
            
            # Recalculate and verify event hash
            calculated_hash = self._calculate_event_hash(event)
            if calculated_hash != event.event_hash:
                invalid_hashes.append({
                    "event_id": event.id,
                    "timestamp": event.event_timestamp.isoformat(),
                    "stored_hash": event.event_hash,
                    "calculated_hash": calculated_hash
                })
            
            previous_hash = event.event_hash
        
        is_valid = len(broken_links) == 0 and len(invalid_hashes) == 0
        
        return {
            "valid": is_valid,
            "total_events": len(events),
            "broken_links": broken_links,
            "invalid_hashes": invalid_hashes,
            "message": "Chain integrity verified" if is_valid else "Chain integrity compromised"
        }
    
    def calculate_data_fingerprint(self, data: Any) -> str:
        """Calculate SHA-256 fingerprint of data."""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True, default=str)
        else:
            data_str = str(data)
        
        return hashlib.sha256(data_str.encode()).hexdigest()
