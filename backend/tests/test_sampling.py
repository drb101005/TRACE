"""Test deterministic sampling service."""
import pytest
from datetime import datetime
from app.services.sampling import SamplingService
from app.db import models
from app.domain.enums import UserRole


def create_test_transactions(db_session, engagement_id, source_version_id, count=100):
    """Create test transactions for sampling."""
    transactions = []
    
    for i in range(count):
        txn = models.Transaction(
            source_version_id=source_version_id,
            engagement_id=engagement_id,
            invoice_number=f"INV-{i:04d}",
            invoice_date=datetime(2024, 1, 1 + (i % 90)),
            customer_name=f"Customer-{i % 20}",  # 20 different customers
            gross_amount=1000 + (i * 100),
            tax_amount=(1000 + (i * 100)) * 0.18,
            net_amount=(1000 + (i * 100)) * 0.82,
            is_related_party=(i % 10 == 0),  # 10% related party
            risk_score=float(i % 100) / 100.0  # Risk score 0-0.99
        )
        transactions.append(txn)
        db_session.add(txn)
    
    db_session.commit()
    
    for txn in transactions:
        db_session.refresh(txn)
    
    return transactions


def test_sales_tod_sampling_reproducibility(db_session, test_users):
    """Test that sampling with same seed produces same results."""
    # Create engagement
    client = test_users[UserRole.CLIENT_EMPLOYEE]
    engagement = models.Engagement(
        name="Test Engagement",
        client_name="Test Co",
        client_user_id=client.id,
        reporting_period_start=datetime(2023, 4, 1),
        reporting_period_end=datetime(2024, 3, 31)
    )
    db_session.add(engagement)
    db_session.commit()
    db_session.refresh(engagement)
    
    # Create source artifact and version
    artifact = models.SourceArtifact(
        engagement_id=engagement.id,
        original_filename="test.csv",
        safe_filename="test_safe.csv",
        file_type="csv",
        size_bytes=1000,
        sha256_hash="test_hash",
        storage_path="/tmp/test.csv",
        uploader_id=client.id
    )
    db_session.add(artifact)
    db_session.commit()
    db_session.refresh(artifact)
    
    version = models.SourceVersion(
        artifact_id=artifact.id,
        version_number=1,
        extraction_method="pandas_csv"
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)
    
    # Create transactions
    transactions = create_test_transactions(
        db_session, engagement.id, version.id, count=100
    )
    
    # Create snapshot
    snapshot = models.PopulationSnapshot(
        engagement_id=engagement.id,
        snapshot_name="Test Snapshot",
        reporting_period_start=datetime(2023, 4, 1),
        reporting_period_end=datetime(2024, 3, 31),
        total_records=len(transactions),
        total_amount=sum(t.gross_amount for t in transactions),
        source_version_ids=[version.id],
        population_fingerprint="test_fingerprint"
    )
    db_session.add(snapshot)
    db_session.commit()
    db_session.refresh(snapshot)
    
    # Run sampling twice with same seed
    sampling_service = SamplingService(db_session)
    seed = 12345
    
    samples1, meta1 = sampling_service.select_sales_tod_sample(
        snapshot.id, target_count=30, random_seed=seed
    )
    
    samples2, meta2 = sampling_service.select_sales_tod_sample(
        snapshot.id, target_count=30, random_seed=seed
    )
    
    # Extract transaction IDs
    txn_ids1 = [s.transaction_id for s in samples1]
    txn_ids2 = [s.transaction_id for s in samples2]
    
    # Assert same samples selected in same order
    assert txn_ids1 == txn_ids2
    assert meta1["random_seed"] == meta2["random_seed"]
    assert meta1["actual_count"] == meta2["actual_count"]


def test_sales_tod_target_count(db_session, test_users):
    """Test that sampling respects target count."""
    # Setup (similar to above)
    client = test_users[UserRole.CLIENT_EMPLOYEE]
    engagement = models.Engagement(
        name="Test Engagement",
        client_name="Test Co",
        client_user_id=client.id,
        reporting_period_start=datetime(2023, 4, 1),
        reporting_period_end=datetime(2024, 3, 31)
    )
    db_session.add(engagement)
    db_session.commit()
    db_session.refresh(engagement)
    
    artifact = models.SourceArtifact(
        engagement_id=engagement.id,
        original_filename="test.csv",
        safe_filename="test_safe.csv",
        file_type="csv",
        size_bytes=1000,
        sha256_hash="test_hash",
        storage_path="/tmp/test.csv",
        uploader_id=client.id
    )
    db_session.add(artifact)
    db_session.commit()
    db_session.refresh(artifact)
    
    version = models.SourceVersion(
        artifact_id=artifact.id,
        version_number=1,
        extraction_method="pandas_csv"
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)
    
    transactions = create_test_transactions(
        db_session, engagement.id, version.id, count=100
    )
    
    snapshot = models.PopulationSnapshot(
        engagement_id=engagement.id,
        snapshot_name="Test Snapshot",
        reporting_period_start=datetime(2023, 4, 1),
        reporting_period_end=datetime(2024, 3, 31),
        total_records=len(transactions),
        source_version_ids=[version.id],
        population_fingerprint="test_fingerprint"
    )
    db_session.add(snapshot)
    db_session.commit()
    db_session.refresh(snapshot)
    
    # Test default target (30)
    sampling_service = SamplingService(db_session)
    samples, metadata = sampling_service.select_sales_tod_sample(snapshot.id)
    
    assert metadata["target_count"] == 30
    assert metadata["actual_count"] <= 30
    assert len(samples) == metadata["actual_count"]


def test_cutoff_sampling(db_session, test_users):
    """Test cut-off sample selection."""
    # Setup
    client = test_users[UserRole.CLIENT_EMPLOYEE]
    engagement = models.Engagement(
        name="Test Engagement",
        client_name="Test Co",
        client_user_id=client.id,
        reporting_period_start=datetime(2023, 4, 1),
        reporting_period_end=datetime(2024, 3, 31)
    )
    db_session.add(engagement)
    db_session.commit()
    db_session.refresh(engagement)
    
    artifact = models.SourceArtifact(
        engagement_id=engagement.id,
        original_filename="test.csv",
        safe_filename="test_safe.csv",
        file_type="csv",
        size_bytes=1000,
        sha256_hash="test_hash",
        storage_path="/tmp/test.csv",
        uploader_id=client.id
    )
    db_session.add(artifact)
    db_session.commit()
    db_session.refresh(artifact)
    
    version = models.SourceVersion(
        artifact_id=artifact.id,
        version_number=1,
        extraction_method="pandas_csv"
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)
    
    transactions = create_test_transactions(
        db_session, engagement.id, version.id, count=50
    )
    
    snapshot = models.PopulationSnapshot(
        engagement_id=engagement.id,
        snapshot_name="Test Snapshot",
        reporting_period_start=datetime(2023, 4, 1),
        reporting_period_end=datetime(2024, 3, 31),
        total_records=len(transactions),
        source_version_ids=[version.id],
        population_fingerprint="test_fingerprint"
    )
    db_session.add(snapshot)
    db_session.commit()
    db_session.refresh(snapshot)
    
    # Run cut-off sampling
    sampling_service = SamplingService(db_session)
    cutoff_date = datetime(2024, 3, 31)
    
    samples, metadata = sampling_service.select_cutoff_tod_sample(
        snapshot.id, cutoff_date, random_seed=12345
    )
    
    # Verify samples exist
    assert len(samples) > 0
    assert metadata["pre_cutoff_actual"] >= 0
    assert metadata["post_cutoff_actual"] >= 0
