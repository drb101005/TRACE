"""MCP Server with narrow typed audit tools."""
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db import models
from app.domain.enums import UserRole
from app.core.errors import AuthorizationException


class AuditMCPServer:
    """
    MCP Server for audit inspection with server-side authorization.
    
    Tools are read-only for external judge agents.
    AI Auditor role cannot mutate business data or approve findings.
    """
    
    def __init__(self):
        self.server = Server("trace-audit-server")
        self.current_user_id: str = None
        self.current_user_role: UserRole = None
        
        # Register tools
        self._register_tools()
    
    def set_identity(self, user_id: str, role: UserRole):
        """Set authenticated identity (server-side only)."""
        self.current_user_id = user_id
        self.current_user_role = role
    
    def _check_permission(self, required_roles: List[UserRole], action: str):
        """Check if current user has permission."""
        if not self.current_user_id or not self.current_user_role:
            raise AuthorizationException("Authentication required")
        
        if self.current_user_role not in required_roles:
            raise AuthorizationException(
                f"Access denied. {action} requires: {', '.join(r.value for r in required_roles)}"
            )
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available audit tools."""
            return [
                Tool(
                    name="get_engagement",
                    description="Get engagement details and status",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "engagement_id": {"type": "string"}
                        },
                        "required": ["engagement_id"]
                    }
                ),
                Tool(
                    name="search_transactions",
                    description="Search transactions with filters",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "engagement_id": {"type": "string"},
                            "customer_name": {"type": "string"},
                            "invoice_number": {"type": "string"},
                            "min_amount": {"type": "number"},
                            "max_amount": {"type": "number"},
                            "limit": {"type": "integer", "default": 100}
                        },
                        "required": ["engagement_id"]
                    }
                ),
                Tool(
                    name="get_sampling_results",
                    description="Get sample selection results and methodology",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sampling_run_id": {"type": "string"}
                        },
                        "required": ["sampling_run_id"]
                    }
                ),
                Tool(
                    name="get_findings",
                    description="Get audit findings for an engagement",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "engagement_id": {"type": "string"},
                            "status": {"type": "string"}
                        },
                        "required": ["engagement_id"]
                    }
                ),
                Tool(
                    name="verify_audit_integrity",
                    description="Verify audit event hash chain integrity",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "engagement_id": {"type": "string"}
                        }
                    }
                ),
                Tool(
                    name="get_related_parties",
                    description="Get related party matching results",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "engagement_id": {"type": "string"}
                        },
                        "required": ["engagement_id"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Execute tool with authorization checks."""
            db = SessionLocal()
            
            try:
                # All tools require authentication
                if name == "get_engagement":
                    return await self._get_engagement(db, arguments)
                
                elif name == "search_transactions":
                    return await self._search_transactions(db, arguments)
                
                elif name == "get_sampling_results":
                    return await self._get_sampling_results(db, arguments)
                
                elif name == "get_findings":
                    return await self._get_findings(db, arguments)
                
                elif name == "verify_audit_integrity":
                    return await self._verify_audit_integrity(db, arguments)
                
                elif name == "get_related_parties":
                    return await self._get_related_parties(db, arguments)
                
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
            
            finally:
                db.close()
    
    async def _get_engagement(self, db: Session, args: Dict) -> List[TextContent]:
        """Get engagement details."""
        # Auditors and admins can view all engagements
        self._check_permission(
            [UserRole.INDEPENDENT_AI_AUDITOR, UserRole.HUMAN_AUDITOR, UserRole.PLATFORM_ADMIN],
            "View engagement"
        )
        
        engagement = db.query(models.Engagement).filter(
            models.Engagement.id == args["engagement_id"]
        ).first()
        
        if not engagement:
            return [TextContent(type="text", text="Engagement not found")]
        
        result = {
            "id": engagement.id,
            "name": engagement.name,
            "client_name": engagement.client_name,
            "status": engagement.status.value,
            "reporting_period": {
                "start": engagement.reporting_period_start.isoformat(),
                "end": engagement.reporting_period_end.isoformat()
            }
        }
        
        import json
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    async def _search_transactions(self, db: Session, args: Dict) -> List[TextContent]:
        """Search transactions."""
        self._check_permission(
            [UserRole.INDEPENDENT_AI_AUDITOR, UserRole.HUMAN_AUDITOR, UserRole.PLATFORM_ADMIN],
            "Search transactions"
        )
        
        query = db.query(models.Transaction).filter(
            models.Transaction.engagement_id == args["engagement_id"]
        )
        
        # Apply filters
        if "customer_name" in args:
            query = query.filter(models.Transaction.customer_name.like(f"%{args['customer_name']}%"))
        
        if "invoice_number" in args:
            query = query.filter(models.Transaction.invoice_number == args["invoice_number"])
        
        if "min_amount" in args:
            query = query.filter(models.Transaction.gross_amount >= args["min_amount"])
        
        if "max_amount" in args:
            query = query.filter(models.Transaction.gross_amount <= args["max_amount"])
        
        # Limit results
        limit = min(args.get("limit", 100), 1000)  # Max 1000
        transactions = query.limit(limit).all()
        
        results = [{
            "id": t.id,
            "invoice_number": t.invoice_number,
            "invoice_date": t.invoice_date.isoformat() if t.invoice_date else None,
            "customer_name": t.customer_name,
            "gross_amount": t.gross_amount,
            "is_related_party": t.is_related_party
        } for t in transactions]
        
        import json
        return [TextContent(
            type="text",
            text=json.dumps({"count": len(results), "transactions": results}, indent=2)
        )]
    
    async def _get_sampling_results(self, db: Session, args: Dict) -> List[TextContent]:
        """Get sampling results."""
        self._check_permission(
            [UserRole.INDEPENDENT_AI_AUDITOR, UserRole.HUMAN_AUDITOR, UserRole.PLATFORM_ADMIN],
            "View sampling results"
        )
        
        sampling_run = db.query(models.SamplingRun).filter(
            models.SamplingRun.id == args["sampling_run_id"]
        ).first()
        
        if not sampling_run:
            return [TextContent(type="text", text="Sampling run not found")]
        
        samples = db.query(models.Sample).filter(
            models.Sample.sampling_run_id == sampling_run.id
        ).all()
        
        result = {
            "sampling_run_id": sampling_run.id,
            "sampling_type": sampling_run.sampling_type,
            "algorithm_version": sampling_run.algorithm_version,
            "random_seed": sampling_run.random_seed,
            "target_count": sampling_run.target_count,
            "actual_count": sampling_run.actual_count,
            "coverage_summary": sampling_run.coverage_summary,
            "samples": [{
                "transaction_id": s.transaction_id,
                "selection_reasons": s.selection_reasons,
                "risk_factors": s.risk_factors
            } for s in samples]
        }
        
        import json
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    async def _get_findings(self, db: Session, args: Dict) -> List[TextContent]:
        """Get audit findings."""
        self._check_permission(
            [UserRole.INDEPENDENT_AI_AUDITOR, UserRole.HUMAN_AUDITOR, UserRole.PLATFORM_ADMIN],
            "View findings"
        )
        
        query = db.query(models.Finding).filter(
            models.Finding.engagement_id == args["engagement_id"]
        )
        
        if "status" in args:
            query = query.filter(models.Finding.status == args["status"])
        
        findings = query.all()
        
        results = [{
            "id": f.id,
            "title": f.title,
            "severity": f.severity.value,
            "status": f.status.value,
            "amount_under_review": f.amount_under_review,
            "potential_misstatement": f.potential_misstatement
        } for f in findings]
        
        import json
        return [TextContent(
            type="text",
            text=json.dumps({"count": len(results), "findings": results}, indent=2)
        )]
    
    async def _verify_audit_integrity(self, db: Session, args: Dict) -> List[TextContent]:
        """Verify audit chain integrity."""
        self._check_permission(
            [UserRole.INDEPENDENT_AI_AUDITOR, UserRole.HUMAN_AUDITOR, UserRole.PLATFORM_ADMIN],
            "Verify audit integrity"
        )
        
        from app.services.audit_log import AuditLogService
        audit_log = AuditLogService(db)
        
        result = audit_log.verify_chain_integrity(
            engagement_id=args.get("engagement_id")
        )
        
        import json
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    async def _get_related_parties(self, db: Session, args: Dict) -> List[TextContent]:
        """Get related party matches."""
        self._check_permission(
            [UserRole.INDEPENDENT_AI_AUDITOR, UserRole.HUMAN_AUDITOR, UserRole.PLATFORM_ADMIN],
            "View related parties"
        )
        
        matches = db.query(models.RelatedPartyMatch).filter(
            models.RelatedPartyMatch.engagement_id == args["engagement_id"]
        ).all()
        
        results = [{
            "customer": m.transaction_customer,
            "related_party": m.related_party_name,
            "match_status": m.match_status.value,
            "match_score": m.match_score,
            "match_reason": m.match_reason
        } for m in matches]
        
        import json
        return [TextContent(
            type="text",
            text=json.dumps({"count": len(results), "matches": results}, indent=2)
        )]
    
    async def run(self):
        """Run MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


# Entry point for MCP server
async def main():
    """Main entry point for MCP server."""
    server = AuditMCPServer()
    
    # For demo, set default identity (in production, authenticate first)
    # This would come from a trusted authentication mechanism
    server.set_identity(
        user_id="ai_auditor",
        role=UserRole.INDEPENDENT_AI_AUDITOR
    )
    
    await server.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
