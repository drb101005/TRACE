"""Seed database with demo users and test data."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from app.db.database import SessionLocal, init_db
from app.db import models
from app.domain.enums import UserRole
from app.core.security import get_password_hash


def seed_users(db):
    """Create demo users for each role."""
    print("Creating demo users...")
    
    users = [
        {
            "username": "client_user",
            "email": "client@example.com",
            "password": "password123",
            "role": UserRole.CLIENT_EMPLOYEE,
            "full_name": "John Client"
        },
        {
            "username": "ai_auditor",
            "email": "ai.auditor@example.com",
            "password": "password123",
            "role": UserRole.INDEPENDENT_AI_AUDITOR,
            "full_name": "AI Auditor System"
        },
        {
            "username": "human_auditor",
            "email": "auditor@example.com",
            "password": "password123",
            "role": UserRole.HUMAN_AUDITOR,
            "full_name": "Jane Auditor"
        },
        {
            "username": "admin_user",
            "email": "admin@example.com",
            "password": "password123",
            "role": UserRole.PLATFORM_ADMIN,
            "full_name": "Platform Administrator"
        }
    ]
    
    created_users = {}
    for user_data in users:
        # Check if user exists
        existing = db.query(models.User).filter(
            models.User.username == user_data["username"]
        ).first()
        
        if existing:
            print(f"  - User {user_data['username']} already exists")
            created_users[user_data["role"]] = existing
            continue
        
        user = models.User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            role=user_data["role"],
            full_name=user_data["full_name"]
        )
        db.add(user)
        created_users[user_data["role"]] = user
        print(f"  ✓ Created user: {user_data['username']} ({user_data['role'].value})")
    
    db.commit()
    
    # Refresh to get IDs
    for user in created_users.values():
        db.refresh(user)
    
    return created_users


def seed_engagement(db, client_user):
    """Create a demo engagement."""
    print("\nCreating demo engagement...")
    
    # Check if engagement exists
    existing = db.query(models.Engagement).filter(
        models.Engagement.name == "Demo Manufacturing Audit FY2024"
    ).first()
    
    if existing:
        print("  - Engagement already exists")
        return existing
    
    # Create engagement for FY 2023-2024 (Apr 1, 2023 - Mar 31, 2024)
    engagement = models.Engagement(
        name="Demo Manufacturing Audit FY2024",
        client_name="Demo Manufacturing Ltd",
        client_user_id=client_user.id,
        reporting_period_start=datetime(2023, 4, 1),
        reporting_period_end=datetime(2024, 3, 31),
        description="Synthetic demo engagement with planted anomalies for testing"
    )
    
    db.add(engagement)
    db.commit()
    db.refresh(engagement)
    
    print(f"  ✓ Created engagement: {engagement.name}")
    return engagement


def seed_compliance_references(db):
    """Create sample compliance references."""
    print("\nCreating compliance references...")
    
    references = [
        {
            "authority_name": "ICAI",
            "title": "SA 530 - Audit Sampling",
            "version": "2023",
            "section_clause": "Overall",
            "verification_status": "VERIFIED"
        },
        {
            "authority_name": "ICAI",
            "title": "SA 500 - Audit Evidence",
            "version": "2023",
            "section_clause": "Overall",
            "verification_status": "VERIFIED"
        },
        {
            "authority_name": "GST Council",
            "title": "CGST Act 2017",
            "version": "2023",
            "section_clause": "Section 31 - Tax Invoice",
            "verification_status": "VERIFIED"
        },
        {
            "authority_name": "MCA",
            "title": "Ind AS 115 - Revenue from Contracts",
            "version": "2023",
            "section_clause": "Overall",
            "verification_status": "VERIFIED"
        }
    ]
    
    for ref_data in references:
        # Check if exists
        existing = db.query(models.ComplianceReference).filter(
            models.ComplianceReference.authority_name == ref_data["authority_name"],
            models.ComplianceReference.title == ref_data["title"]
        ).first()
        
        if existing:
            continue
        
        ref = models.ComplianceReference(**ref_data)
        db.add(ref)
        print(f"  ✓ Created reference: {ref_data['authority_name']} - {ref_data['title']}")
    
    db.commit()


def create_demo_anomalies_manifest():
    """Create a ground truth manifest of planted anomalies (separate from agent inputs)."""
    print("\nCreating ground truth anomalies manifest...")
    
    manifest_path = Path(__file__).parent.parent / "data" / "demo" / "anomalies_ground_truth.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    
    manifest = {
        "warning": "This file contains ground truth for testing. Keep separate from agent inputs.",
        "anomalies": [
            {
                "type": "missing_dispatch_evidence",
                "invoice_number": "INV-2024-0156",
                "description": "Invoice without matching dispatch/delivery proof"
            },
            {
                "type": "post_period_credit_note",
                "invoice_number": "INV-2024-0089",
                "credit_note": "CN-2024-0012",
                "description": "Credit note issued after year-end for in-period sale"
            },
            {
                "type": "undisclosed_related_party",
                "customer_name": "TechCorp Industries",
                "description": "Related party transaction not initially disclosed"
            },
            {
                "type": "cutoff_exception",
                "invoice_number": "INV-2024-0301",
                "description": "Invoice dated March 30 but goods delivered April 5"
            },
            {
                "type": "duplicate_evidence",
                "invoice_numbers": ["INV-2024-0201", "INV-2024-0202"],
                "description": "Same dispatch document used for two invoices"
            }
        ],
        "expected_findings_count": 5,
        "test_procedures": [
            "invoice_to_dispatch_trace",
            "credit_note_analysis",
            "related_party_matching",
            "cutoff_testing",
            "evidence_uniqueness_check"
        ]
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"  ✓ Created anomalies manifest at: {manifest_path}")
    print("  ⚠ Keep this file separate from agent-accessible inputs!")


def main():
    """Run all seed operations."""
    print("=" * 60)
    print("TRACE Backend - Seed Data Script")
    print("=" * 60)
    
    # Initialize database
    print("\nInitializing database...")
    init_db()
    print("  ✓ Database initialized")
    
    # Create session
    db = SessionLocal()
    
    try:
        # Seed users
        users = seed_users(db)
        
        # Seed engagement
        client_user = users[UserRole.CLIENT_EMPLOYEE]
        engagement = seed_engagement(db, client_user)
        
        # Seed compliance references
        seed_compliance_references(db)
        
        # Create ground truth manifest
        create_demo_anomalies_manifest()
        
        print("\n" + "=" * 60)
        print("✓ Seeding completed successfully!")
        print("=" * 60)
        print("\nDemo Users Created:")
        print("  Username: client_user     | Password: password123 | Role: CLIENT_EMPLOYEE")
        print("  Username: ai_auditor      | Password: password123 | Role: INDEPENDENT_AI_AUDITOR")
        print("  Username: human_auditor   | Password: password123 | Role: HUMAN_AUDITOR")
        print("  Username: admin_user      | Password: password123 | Role: PLATFORM_ADMIN")
        print("\nYou can now start the server with: uvicorn main:app --reload")
        print("API docs available at: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
