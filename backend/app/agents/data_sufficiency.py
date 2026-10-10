"""Data Sufficiency Agent - Assesses audit readiness."""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.agents.base_agent import BaseAgent
from app.db import models
from app.domain.enums import DataSufficiency


class DataSufficiencyAgent(BaseAgent):
    """
    Assess whether each planned procedure can be run on available data.
    """
    
    # Required data for each procedure
    PROCEDURE_REQUIREMENTS = {
        "sales_register_validation": ["invoice_number", "invoice_date", "customer_name", "amount"],
        "related_party_matching": ["customer_name"],
        "sales_tod_sampling": ["invoice_number", "invoice_date", "amount"],
        "cutoff_testing": ["invoice_date", "dispatch_date", "delivery_date"],
        "invoice_to_dispatch_trace": ["invoice_number", "dispatch_number", "delivery_proof"],
        "credit_note_analysis": ["credit_note_number", "credit_note_date", "original_invoice"],
        "reconciliation": ["register_amount", "ledger_amount"]
    }
    
    def __init__(self, engagement_id: str, db: Session):
        super().__init__("DATA_SUFFICIENCY", engagement_id)
        self.db = db
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess data sufficiency for planned procedures.
        
        Returns:
            {
                "overall_status": "SUFFICIENT | CONDITIONALLY_SUFFICIENT | INSUFFICIENT",
                "procedure_results": [...],
                "missing_inputs": [...],
                "limitations": [...],
                "evidence_requests": [...]
            }
        """
        # Get engagement
        engagement = self.db.query(models.Engagement).filter(
            models.Engagement.id == self.engagement_id
        ).first()
        
        if not engagement:
            return {
                "status": "ERROR",
                "message": "Engagement not found"
            }
        
        # Get uploaded artifacts
        artifacts = self.db.query(models.SourceArtifact).filter(
            models.SourceArtifact.engagement_id == self.engagement_id
        ).all()
        
        # Assess each procedure
        procedure_results = []
        missing_inputs = []
        limitations = []
        evidence_requests = []
        
        for procedure, required_fields in self.PROCEDURE_REQUIREMENTS.items():
            result = self._assess_procedure(
                procedure, required_fields, artifacts
            )
            procedure_results.append(result)
            
            if result["status"] == DataSufficiency.INSUFFICIENT:
                missing_inputs.extend(result["missing"])
            
            if result["limitations"]:
                limitations.extend(result["limitations"])
        
        # Determine overall status
        statuses = [p["status"] for p in procedure_results]
        
        if all(s == DataSufficiency.SUFFICIENT for s in statuses):
            overall = DataSufficiency.SUFFICIENT
        elif any(s == DataSufficiency.INSUFFICIENT for s in statuses):
            overall = DataSufficiency.INSUFFICIENT
        else:
            overall = DataSufficiency.CONDITIONALLY_SUFFICIENT
        
        # Create assessment record
        assessment = models.DataSufficiencyAssessment(
            engagement_id=self.engagement_id,
            overall_status=overall,
            procedure_results=[{
                "procedure": p["procedure"],
                "status": p["status"].value,
                "blockers": p["blockers"],
                "missing": p["missing"]
            } for p in procedure_results],
            missing_inputs=list(set(missing_inputs)),
            limitations=limitations,
            assessed_by=self.agent_type
        )
        
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        
        return {
            "assessment_id": assessment.id,
            "overall_status": overall.value,
            "procedure_results": procedure_results,
            "missing_inputs": list(set(missing_inputs)),
            "limitations": limitations,
            "evidence_requests": evidence_requests
        }
    
    def _assess_procedure(
        self,
        procedure: str,
        required_fields: List[str],
        artifacts: List[models.SourceArtifact]
    ) -> Dict[str, Any]:
        """Assess if a specific procedure can be executed."""
        blockers = []
        missing = []
        limitations = []
        
        # Check if we have any uploads
        if not artifacts:
            blockers.append("No files uploaded")
            missing.extend(required_fields)
            return {
                "procedure": procedure,
                "status": DataSufficiency.INSUFFICIENT,
                "blockers": blockers,
                "missing": missing,
                "limitations": limitations
            }
        
        # Check for extracted data
        has_csv_xlsx = any(
            a.file_type.value in ["csv", "xlsx"] for a in artifacts
        )
        
        if not has_csv_xlsx:
            blockers.append("No structured data files (CSV/XLSX) uploaded")
            missing.extend(required_fields)
        
        # For this demo, if we have CSV/XLSX, consider basic procedures sufficient
        # In production, would validate actual column presence
        if procedure in ["sales_register_validation", "sales_tod_sampling", "related_party_matching"]:
            if has_csv_xlsx:
                status = DataSufficiency.SUFFICIENT
            else:
                status = DataSufficiency.INSUFFICIENT
        else:
            # Advanced procedures may need more data
            status = DataSufficiency.CONDITIONALLY_SUFFICIENT
            limitations.append(f"{procedure} requires additional evidence documents")
        
        return {
            "procedure": procedure,
            "status": status,
            "blockers": blockers,
            "missing": missing,
            "limitations": limitations
        }
