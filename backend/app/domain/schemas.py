"""Pydantic schemas for API requests and responses."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.domain.enums import (
    UserRole, EngagementStatus, FileType, DataSufficiency,
    MatchStatus, EvidenceStatus, CheckStatus, FindingSeverity,
    FindingStatus, ComplianceStatus, AgentType
)


# User schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: UserRole
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    username: str
    password: str


# Engagement schemas
class EngagementCreate(BaseModel):
    name: str
    client_name: str
    reporting_period_start: datetime
    reporting_period_end: datetime
    description: Optional[str] = None


class EngagementUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[EngagementStatus] = None
    description: Optional[str] = None


class EngagementResponse(BaseModel):
    id: str
    name: str
    client_name: str
    client_user_id: Optional[str]
    reporting_period_start: datetime
    reporting_period_end: datetime
    status: EngagementStatus
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Upload schemas
class UploadResponse(BaseModel):
    id: str
    engagement_id: str
    original_filename: str
    file_type: FileType
    size_bytes: int
    sha256_hash: str
    upload_timestamp: datetime
    version_number: int
    
    model_config = ConfigDict(from_attributes=True)


class ValidationResult(BaseModel):
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    duplicate_candidates: List[Dict[str, Any]] = []
    total_records: int
    total_amount: Optional[float] = None
    date_range: Optional[Dict[str, Any]] = None
    missing_fields: List[str] = []


# Sufficiency schemas
class ProcedureReadiness(BaseModel):
    procedure_name: str
    status: DataSufficiency
    blockers: List[str] = []
    missing_inputs: List[str] = []
    limitations: List[str] = []


class SufficiencyAssessmentResponse(BaseModel):
    id: str
    engagement_id: str
    overall_status: DataSufficiency
    assessment_timestamp: datetime
    procedure_results: List[ProcedureReadiness]
    evidence_requests: List[str] = []
    
    model_config = ConfigDict(from_attributes=True)


# Related party schemas
class RelatedPartyMatchResponse(BaseModel):
    id: str
    transaction_customer: str
    related_party_name: str
    match_status: MatchStatus
    match_score: Optional[float]
    match_reason: Optional[str]
    effective_date: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


# Snapshot schemas
class SnapshotCreate(BaseModel):
    snapshot_name: str
    inclusion_criteria: Optional[str] = None
    exclusion_criteria: Optional[str] = None


class SnapshotResponse(BaseModel):
    id: str
    engagement_id: str
    snapshot_name: str
    snapshot_timestamp: datetime
    total_records: int
    total_amount: Optional[float]
    population_fingerprint: str
    
    model_config = ConfigDict(from_attributes=True)


# Sampling schemas
class SamplingRequest(BaseModel):
    snapshot_id: str
    sampling_type: str  # "SALES_TOD" or "CUTOFF_TOD"
    target_count: Optional[int] = 30
    random_seed: Optional[int] = None


class SampleResponse(BaseModel):
    id: str
    transaction_id: str
    selection_reasons: List[str]
    risk_factors: Optional[Dict[str, Any]]
    stratum: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class SamplingRunResponse(BaseModel):
    id: str
    snapshot_id: str
    sampling_type: str
    algorithm_version: str
    random_seed: Optional[int]
    target_count: int
    actual_count: int
    coverage_summary: Optional[str]
    executed_at: datetime
    samples: List[SampleResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


# Evidence schemas
class EvidenceRequestCreate(BaseModel):
    sample_id: str
    evidence_type: str
    description: Optional[str] = None


class EvidenceRequestResponse(BaseModel):
    id: str
    sample_id: str
    evidence_type: str
    description: Optional[str]
    status: EvidenceStatus
    requested_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Audit check schemas
class AuditCheckResponse(BaseModel):
    id: str
    engagement_id: str
    check_name: str
    check_type: str
    rule_id: str
    rule_version: str
    status: CheckStatus
    executed_at: datetime
    result_summary: Optional[str]
    limitations: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


# Finding schemas
class FindingCreate(BaseModel):
    title: str
    description: str
    rule_id: str
    rule_version: str
    severity: FindingSeverity
    amount_under_review: Optional[float] = None
    potential_misstatement: Optional[float] = None
    affected_transaction_ids: Optional[List[str]] = []
    affected_sample_ids: Optional[List[str]] = []
    evidence_ids: Optional[List[str]] = []
    expected_value: Optional[str] = None
    observed_value: Optional[str] = None
    rationale: Optional[str] = None
    limitations: Optional[str] = None


class FindingResponse(BaseModel):
    id: str
    engagement_id: str
    version_number: int
    title: str
    description: str
    severity: FindingSeverity
    status: FindingStatus
    amount_under_review: Optional[float]
    potential_misstatement: Optional[float]
    confirmed_misstatement: Optional[float]
    proposed_adjustment: Optional[float]
    approved_adjustment: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Review schemas
class ReviewDecisionCreate(BaseModel):
    finding_id: str
    finding_version: int
    decision: str  # APPROVE, REJECT, REOPEN, REQUEST_MORE_EVIDENCE
    comments: Optional[str] = None
    approved_adjustment: Optional[float] = None


class ReviewDecisionResponse(BaseModel):
    id: str
    finding_id: str
    finding_version: int
    decision: str
    comments: Optional[str]
    approved_adjustment: Optional[float]
    decided_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Compliance schemas
class ComplianceProcedureResponse(BaseModel):
    id: str
    engagement_id: str
    procedure_name: str
    status: ComplianceStatus
    notes: Optional[str]
    limitations: Optional[str]
    assessed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Agent schemas
class AgentRunRequest(BaseModel):
    agent_type: AgentType
    input_data: Optional[Dict[str, Any]] = None


class AgentRunResponse(BaseModel):
    id: str
    engagement_id: str
    agent_type: AgentType
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    output_data: Optional[Dict[str, Any]]
    errors: Optional[List[Dict[str, Any]]]
    
    model_config = ConfigDict(from_attributes=True)


# Transaction schemas
class TransactionResponse(BaseModel):
    id: str
    invoice_number: Optional[str]
    invoice_date: Optional[datetime]
    customer_name: Optional[str]
    gross_amount: Optional[float]
    tax_amount: Optional[float]
    net_amount: Optional[float]
    currency: str
    is_related_party: Optional[bool]
    risk_score: Optional[float]
    is_sampled: bool
    
    model_config = ConfigDict(from_attributes=True)


# Audit event schemas
class AuditEventResponse(BaseModel):
    id: str
    event_timestamp: datetime
    actor_id: str
    actor_role: UserRole
    action: str
    target_type: str
    target_id: str
    event_hash: str
    previous_event_hash: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


# Health check
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "0.1.0"
    llm_available: bool
    ocr_available: bool
