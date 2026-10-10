"""SQLAlchemy database models."""
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, Boolean, 
    ForeignKey, Enum as SQLEnum, Index, JSON
)
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.domain.enums import (
    UserRole, EngagementStatus, FileType, ExtractionMethod,
    DataSufficiency, MatchStatus, SampleSelectionReason,
    EvidenceStatus, CheckStatus, FindingSeverity, FindingStatus,
    ComplianceStatus, AuditEventAction, AgentType
)
import uuid


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


class User(Base):
    """User account with role-based permissions."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    engagements = relationship("Engagement", back_populates="client_user", foreign_keys="Engagement.client_user_id")


class Engagement(Base):
    """Audit engagement representing a client audit project."""
    __tablename__ = "engagements"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    client_name = Column(String, nullable=False)
    client_user_id = Column(String, ForeignKey("users.id"))
    reporting_period_start = Column(DateTime, nullable=False)
    reporting_period_end = Column(DateTime, nullable=False)
    status = Column(SQLEnum(EngagementStatus), default=EngagementStatus.DRAFT)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client_user = relationship("User", back_populates="engagements", foreign_keys=[client_user_id])
    uploads = relationship("SourceArtifact", back_populates="engagement")
    snapshots = relationship("PopulationSnapshot", back_populates="engagement")
    findings = relationship("Finding", back_populates="engagement")
    agent_runs = relationship("AgentRun", back_populates="engagement")
    
    __table_args__ = (
        Index("idx_engagement_client", "client_user_id"),
        Index("idx_engagement_status", "status"),
    )


class SourceArtifact(Base):
    """Original uploaded file with immutable storage."""
    __tablename__ = "source_artifacts"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    engagement_id = Column(String, ForeignKey("engagements.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    safe_filename = Column(String, nullable=False)
    file_type = Column(SQLEnum(FileType), nullable=False)
    mime_type = Column(String)
    size_bytes = Column(Integer, nullable=False)
    sha256_hash = Column(String, nullable=False, index=True)
    storage_path = Column(String, nullable=False)
    uploader_id = Column(String, ForeignKey("users.id"))
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    version_number = Column(Integer, default=1)
    replaces_artifact_id = Column(String, ForeignKey("source_artifacts.id"))
    
    # Relationships
    engagement = relationship("Engagement", back_populates="uploads")
    versions = relationship("SourceVersion", back_populates="artifact")
    
    __table_args__ = (
        Index("idx_artifact_engagement", "engagement_id"),
        Index("idx_artifact_hash", "sha256_hash"),
    )


class SourceVersion(Base):
    """Versioned parsed/normalized data from source artifacts."""
    __tablename__ = "source_versions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    artifact_id = Column(String, ForeignKey("source_artifacts.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    extraction_method = Column(SQLEnum(ExtractionMethod), nullable=False)
    extraction_timestamp = Column(DateTime, default=datetime.utcnow)
    extraction_confidence = Column(Float)
    parser_version = Column(String)
    sheet_name = Column(String)
    page_number = Column(Integer)
    row_count = Column(Integer)
    column_count = Column(Integer)
    data_fingerprint = Column(String)
    metadata_json = Column(JSON)
    
    # Relationships
    artifact = relationship("SourceArtifact", back_populates="versions")
    transactions = relationship("Transaction", back_populates="source_version")
    
    __table_args__ = (
        Index("idx_version_artifact", "artifact_id"),
    )


class Transaction(Base):
    """Normalized business transaction record."""
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    source_version_id = Column(String, ForeignKey("source_versions.id"), nullable=False)
    engagement_id = Column(String, ForeignKey("engagements.id"), nullable=False)
    
    # Transaction identifiers
    invoice_number = Column(String, index=True)
    invoice_date = Column(DateTime)
    customer_name = Column(String, index=True)
    customer_id = Column(String)
    
    # Amounts
    gross_amount = Column(Float)
    tax_amount = Column(Float)
    net_amount = Column(Float)
    currency = Column(String, default="INR")
    
    # Provenance
    source_row_number = Column(Integer)
    source_cell_reference = Column(String)
    
    # Related party status
    is_related_party = Column(Boolean)
    related_party_match_id = Column(String, ForeignKey("related_party_matches.id"))
    
    # Audit metadata
    risk_score = Column(Float)
    is_sampled = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    source_version = relationship("SourceVersion", back_populates="transactions")
    samples = relationship("Sample", back_populates="transaction")
    
    __table_args__ = (
        Index("idx_transaction_engagement", "engagement_id"),
        Index("idx_transaction_invoice", "invoice_number"),
        Index("idx_transaction_customer", "customer_name"),
        Index("idx_transaction_date", "invoice_date"),
    )


class RelatedPartyMatch(Base):
    """Related party matching results with provenance."""
    __tablename__ = "related_party_matches"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    engagement_id = Column(String, ForeignKey("engagements.id"), nullable=False)
    transaction_customer = Column(String, nullable=False)
    related_party_name = Column(String, nullable=False)
    match_status = Column(SQLEnum(MatchStatus), nullable=False)
    match_score = Column(Float)
    match_reason = Column(Text)
    effective_date = Column(DateTime)
    matched_at = Column(DateTime, default=datetime.utcnow)
    reviewed_by = Column(String, ForeignKey("users.id"))
    
    __table_args__ = (
        Index("idx_rp_match_engagement", "engagement_id"),
    )


class PopulationSnapshot(Base):
    """Frozen population for sampling with fingerprint."""
    __tablename__ = "population_snapshots"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    engagement_id = Column(String, ForeignKey("engagements.id"), nullable=False)
    snapshot_name = Column(String, nullable=False)
    snapshot_timestamp = Column(DateTime, default=datetime.utcnow)
    reporting_period_start = Column(DateTime, nullable=False)
    reporting_period_end = Column(DateTime, nullable=False)
    
    # Population metadata
    total_records = Column(Integer, nullable=False)
    total_amount = Column(Float)
    inclusion_criteria = Column(Text)
    exclusion_criteria = Column(Text)
    source_version_ids = Column(JSON)  # List of source version IDs
    
    # Fingerprint for reproducibility
    population_fingerprint = Column(String, nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    engagement = relationship("Engagement", back_populates="snapshots")
    sampling_runs = relationship("SamplingRun", back_populates="snapshot")
    
    __table_args__ = (
        Index("idx_snapshot_engagement", "engagement_id"),
    )


class SamplingRun(Base):
    """Sample selection execution with reproducible parameters."""
    __tablename__ = "sampling_runs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    snapshot_id = Column(String, ForeignKey("population_snapshots.id"), nullable=False)
    sampling_type = Column(String, nullable=False)  # e.g., "SALES_TOD", "CUTOFF_TOD"
    algorithm_version = Column(String, nullable=False)
    random_seed = Column(Integer)
    target_count = Column(Integer)
    actual_count = Column(Integer)
    configuration_json = Column(JSON)
    coverage_summary = Column(Text)
    executed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    snapshot = relationship("PopulationSnapshot", back_populates="sampling_runs")
    samples = relationship("Sample", back_populates="sampling_run")
    
    __table_args__ = (
        Index("idx_sampling_snapshot", "snapshot_id"),
    )


class Sample(Base):
    """Selected sample with selection reasons."""
    __tablename__ = "samples"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    sampling_run_id = Column(String, ForeignKey("sampling_runs.id"), nullable=False)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    selection_reasons = Column(JSON)  # List of SampleSelectionReason
    risk_factors = Column(JSON)
    stratum = Column(String)
    selection_order = Column(Integer)
    
    # Relationships
    sampling_run = relationship("SamplingRun", back_populates="samples")
    transaction = relationship("Transaction", back_populates="samples")
    evidence_requests = relationship("EvidenceRequest", back_populates="sample")
    
    __table_args__ = (
        Index("idx_sample_run", "sampling_run_id"),
        Index("idx_sample_transaction", "transaction_id"),
    )


class EvidenceRequest(Base):
    """Evidence request for a sample."""
    __tablename__ = "evidence_requests"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    sample_id = Column(String, ForeignKey("samples.id"), nullable=False)
    evidence_type = Column(String, nullable=False)  # e.g., "INVOICE", "EWAY_BILL", "LR"
    description = Column(Text)
    status = Column(SQLEnum(EvidenceStatus), default=EvidenceStatus.REQUESTED)
    requested_at = Column(DateTime, default=datetime.utcnow)
    requested_by = Column(String, ForeignKey("users.id"))
    
    # Relationships
    sample = relationship("Sample", back_populates="evidence_requests")
    evidence_artifacts = relationship("EvidenceArtifact", back_populates="request")
    
    __table_args__ = (
        Index("idx_evidence_req_sample", "sample_id"),
    )


class EvidenceArtifact(Base):
    """Uploaded evidence artifact."""
    __tablename__ = "evidence_artifacts"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    request_id = Column(String, ForeignKey("evidence_requests.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    safe_filename = Column(String, nullable=False)
    file_type = Column(SQLEnum(FileType), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sha256_hash = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    extraction_method = Column(SQLEnum(ExtractionMethod))
    extraction_result = Column(JSON)
    extraction_confidence = Column(Float)
    uploaded_by = Column(String, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    request = relationship("EvidenceRequest", back_populates="evidence_artifacts")
    
    __table_args__ = (
        Index("idx_evidence_request", "request_id"),
    )


class AuditCheck(Base):
    """Audit check definition and execution result."""
    __tablename__ = "audit_checks"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    engagement_id = Column(String, ForeignKey("engagements.id"), nullable=False)
    check_name = Column(String, nullable=False)
    check_type = Column(String, nullable=False)
    rule_id = Column(String, nullable=False)
    rule_version = Column(String, nullable=False)
    status = Column(SQLEnum(CheckStatus), nullable=False)
    executed_at = Column(DateTime, default=datetime.utcnow)
    executed_by = Column(String)  # User ID or agent ID
    
    # Check details
    input_parameters = Column(JSON)
    calculation_details = Column(JSON)
    result_summary = Column(Text)
    limitations = Column(Text)
    
    # Source references
    source_ids = Column(JSON)  # List of transaction/evidence IDs
    
    __table_args__ = (
        Index("idx_check_engagement", "engagement_id"),
        Index("idx_check_type", "check_type"),
    )


class Finding(Base):
    """Audit finding with versioning."""
    __tablename__ = "findings"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    engagement_id = Column(String, ForeignKey("engagements.id"), nullable=False)
    version_number = Column(Integer, default=1)
    
    # Finding details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    rule_id = Column(String, nullable=False)
    rule_version = Column(String, nullable=False)
    severity = Column(SQLEnum(FindingSeverity), nullable=False)
    status = Column(SQLEnum(FindingStatus), default=FindingStatus.PENDING_REVIEW)
    
    # Amounts
    gross_transaction_value = Column(Float)
    amount_under_review = Column(Float)
    potential_misstatement = Column(Float)
    confirmed_misstatement = Column(Float)
    proposed_adjustment = Column(Float)
    approved_adjustment = Column(Float)
    currency = Column(String, default="INR")
    
    # References
    affected_transaction_ids = Column(JSON)
    affected_sample_ids = Column(JSON)
    evidence_ids = Column(JSON)
    source_ids = Column(JSON)
    snapshot_id = Column(String, ForeignKey("population_snapshots.id"))
    check_id = Column(String, ForeignKey("audit_checks.id"))
    
    # Metadata
    expected_value = Column(Text)
    observed_value = Column(Text)
    rationale = Column(Text)
    uncertainty = Column(Text)
    limitations = Column(Text)
    no_double_count_group = Column(String)
    
    created_by = Column(String, nullable=False)  # User or agent ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    engagement = relationship("Engagement", back_populates="findings")
    review_decisions = relationship("ReviewDecision", back_populates="finding")
    
    __table_args__ = (
        Index("idx_finding_engagement", "engagement_id"),
        Index("idx_finding_status", "status"),
    )


class ReviewDecision(Base):
    """Human auditor review decision bound to finding version."""
    __tablename__ = "review_decisions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    finding_id = Column(String, ForeignKey("findings.id"), nullable=False)
    finding_version = Column(Integer, nullable=False)
    reviewer_id = Column(String, ForeignKey("users.id"), nullable=False)
    decision = Column(String, nullable=False)  # APPROVE, REJECT, REOPEN, REQUEST_MORE_EVIDENCE
    comments = Column(Text)
    approved_adjustment = Column(Float)
    decided_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    finding = relationship("Finding", back_populates="review_decisions")
    
    __table_args__ = (
        Index("idx_decision_finding", "finding_id"),
    )


class ComplianceReference(Base):
    """Compliance reference with versioned metadata."""
    __tablename__ = "compliance_references"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    authority_name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    version = Column(String)
    effective_date = Column(DateTime)
    section_clause = Column(String)
    source_uri = Column(String)
    document_id = Column(String)
    applicability_rationale = Column(Text)
    verification_status = Column(String)  # VERIFIED, UNVERIFIED, OUTDATED
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_compliance_authority", "authority_name"),
    )


class ComplianceProcedure(Base):
    """Compliance procedure with coverage tracking."""
    __tablename__ = "compliance_procedures"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    engagement_id = Column(String, ForeignKey("engagements.id"), nullable=False)
    procedure_name = Column(String, nullable=False)
    reference_id = Column(String, ForeignKey("compliance_references.id"))
    status = Column(SQLEnum(ComplianceStatus), nullable=False)
    workpaper_ids = Column(JSON)
    evidence_ids = Column(JSON)
    notes = Column(Text)
    limitations = Column(Text)
    assessed_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_procedure_engagement", "engagement_id"),
    )


class AgentRun(Base):
    """Agent execution run with audit trail."""
    __tablename__ = "agent_runs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    engagement_id = Column(String, ForeignKey("engagements.id"), nullable=False)
    agent_type = Column(SQLEnum(AgentType), nullable=False)
    workflow_version = Column(String)
    model_provider = Column(String)
    model_name = Column(String)
    
    # Execution details
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String)  # RUNNING, COMPLETED, FAILED
    
    # Input/output
    input_fingerprint = Column(String)
    input_data = Column(JSON)
    output_data = Column(JSON)
    tool_calls = Column(JSON)  # List of tool invocations
    errors = Column(JSON)
    
    # Relationships
    engagement = relationship("Engagement", back_populates="agent_runs")
    
    __table_args__ = (
        Index("idx_agent_run_engagement", "engagement_id"),
        Index("idx_agent_run_type", "agent_type"),
    )


class AuditEvent(Base):
    """Append-only hash-linked audit event."""
    __tablename__ = "audit_events"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    event_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    actor_id = Column(String, ForeignKey("users.id"), nullable=False)
    actor_role = Column(SQLEnum(UserRole), nullable=False)
    engagement_id = Column(String, ForeignKey("engagements.id"))
    
    # Event details
    action = Column(SQLEnum(AuditEventAction), nullable=False)
    target_type = Column(String, nullable=False)
    target_id = Column(String, nullable=False)
    target_version = Column(Integer)
    
    # Fingerprints
    input_fingerprint = Column(String)
    result_fingerprint = Column(String)
    
    # Hash chain
    previous_event_hash = Column(String)
    event_hash = Column(String, nullable=False, unique=True, index=True)
    
    # Correlation
    correlation_id = Column(String)
    run_id = Column(String)
    
    # Event data
    event_data = Column(JSON)
    
    __table_args__ = (
        Index("idx_event_engagement", "engagement_id"),
        Index("idx_event_actor", "actor_id"),
        Index("idx_event_timestamp", "event_timestamp"),
    )


class DataSufficiencyAssessment(Base):
    """Data sufficiency assessment results."""
    __tablename__ = "data_sufficiency_assessments"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    engagement_id = Column(String, ForeignKey("engagements.id"), nullable=False)
    assessment_timestamp = Column(DateTime, default=datetime.utcnow)
    overall_status = Column(SQLEnum(DataSufficiency), nullable=False)
    
    # Per-procedure results
    procedure_results = Column(JSON)  # Dict of procedure -> status/blockers
    missing_inputs = Column(JSON)
    limitations = Column(JSON)
    evidence_requests = Column(JSON)
    
    assessed_by = Column(String)  # Agent or user ID
    
    __table_args__ = (
        Index("idx_sufficiency_engagement", "engagement_id"),
    )
