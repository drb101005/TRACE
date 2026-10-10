"""Enumeration types for the audit system."""
from enum import Enum


class UserRole(str, Enum):
    """User roles with distinct permissions."""
    CLIENT_EMPLOYEE = "CLIENT_EMPLOYEE"
    INDEPENDENT_AI_AUDITOR = "INDEPENDENT_AI_AUDITOR"
    HUMAN_AUDITOR = "HUMAN_AUDITOR"
    PLATFORM_ADMIN = "PLATFORM_ADMIN"


class EngagementStatus(str, Enum):
    """Engagement workflow states."""
    DRAFT = "draft"
    FILES_RECEIVED = "files_received"
    INGESTION_COMPLETE = "ingestion_complete"
    VALIDATION_COMPLETE = "validation_complete"
    SUFFICIENCY_ASSESSED = "sufficiency_assessed"
    POPULATION_FROZEN = "population_frozen"
    SAMPLING_COMPLETE = "sampling_complete"
    EVIDENCE_COLLECTION = "evidence_collection"
    TESTS_COMPLETE = "tests_complete"
    FINDINGS_PENDING_REVIEW = "findings_pending_review"
    HUMAN_REVIEW = "human_review"
    REPORT_GENERATED = "report_generated"
    APPROVED_FINAL = "approved_final"
    BLOCKED = "blocked"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    SUPERSEDED = "superseded"


class FileType(str, Enum):
    """Supported file types for upload."""
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"
    IMAGE = "image"


class ExtractionMethod(str, Enum):
    """Methods used for data extraction."""
    PANDAS_CSV = "pandas_csv"
    PANDAS_XLSX = "pandas_xlsx"
    OPENPYXL = "openpyxl"
    PYMUPDF_TEXT = "pymupdf_text"
    TESSERACT_OCR = "tesseract_ocr"
    MANUAL = "manual"


class DataSufficiency(str, Enum):
    """Data sufficiency assessment results."""
    SUFFICIENT = "SUFFICIENT"
    CONDITIONALLY_SUFFICIENT = "CONDITIONALLY_SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"


class MatchStatus(str, Enum):
    """Related party matching status."""
    EXACT_MATCH = "EXACT_MATCH"
    FUZZY_MATCH = "FUZZY_MATCH"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    NO_MATCH = "NO_MATCH"


class SampleSelectionReason(str, Enum):
    """Reasons for sample selection."""
    HIGH_RISK = "HIGH_RISK"
    HIGH_VALUE = "HIGH_VALUE"
    RELATED_PARTY = "RELATED_PARTY"
    NON_RELATED_PARTY = "NON_RELATED_PARTY"
    CUTOFF_PRE = "CUTOFF_PRE"
    CUTOFF_POST = "CUTOFF_POST"
    RANDOM_FILL = "RANDOM_FILL"
    CUSTOMER_DIVERSITY = "CUSTOMER_DIVERSITY"
    MANDATORY_COVERAGE = "MANDATORY_COVERAGE"


class EvidenceStatus(str, Enum):
    """Evidence collection and validation status."""
    REQUESTED = "REQUESTED"
    UPLOADED = "UPLOADED"
    EXTRACTED = "EXTRACTED"
    MATCHED = "MATCHED"
    MISMATCHED = "MISMATCHED"
    MISSING = "MISSING"
    UNREADABLE = "UNREADABLE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class CheckStatus(str, Enum):
    """Audit check execution status."""
    PASS = "pass"
    EXCEPTION = "exception"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_APPLICABLE = "not_applicable"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"


class FindingSeverity(str, Enum):
    """Severity levels for audit findings."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"


class FindingStatus(str, Enum):
    """Finding lifecycle status."""
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REOPENED = "REOPENED"
    MORE_EVIDENCE_REQUESTED = "MORE_EVIDENCE_REQUESTED"
    SUPERSEDED = "SUPERSEDED"


class ComplianceStatus(str, Enum):
    """Compliance procedure status."""
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"


class AuditEventAction(str, Enum):
    """Audit event action types."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    FREEZE = "FREEZE"
    UPLOAD = "UPLOAD"
    EXTRACT = "EXTRACT"
    VALIDATE = "VALIDATE"
    SAMPLE = "SAMPLE"
    TEST = "TEST"
    REVIEW = "REVIEW"
    EXPORT = "EXPORT"


class AgentType(str, Enum):
    """Agent types in the system."""
    DATA_SUFFICIENCY = "DATA_SUFFICIENCY"
    SAMPLE_REVIEW = "SAMPLE_REVIEW"
    PRIMARY_EVALUATION = "PRIMARY_EVALUATION"
    COMPLIANCE_CHECKER = "COMPLIANCE_CHECKER"
    REPORT_BRIEF = "REPORT_BRIEF"
