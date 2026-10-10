"""Base agent class with common functionality."""
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import settings


class BaseAgent:
    """Base class for all audit agents."""
    
    def __init__(self, agent_type: str, engagement_id: str):
        self.agent_type = agent_type
        self.engagement_id = engagement_id
        self.llm_available = settings.llm_enabled and bool(settings.gemini_api_key)
    
    def create_run_metadata(self, status: str = "RUNNING") -> Dict[str, Any]:
        """Create standard run metadata."""
        return {
            "agent_type": self.agent_type,
            "engagement_id": self.engagement_id,
            "started_at": datetime.utcnow().isoformat(),
            "status": status,
            "llm_available": self.llm_available,
            "workflow_version": "1.0.0"
        }
    
    def get_llm_client(self):
        """Get LLM client if available."""
        if not self.llm_available:
            return None
        
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            llm = ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                google_api_key=settings.gemini_api_key,
                temperature=0.1  # Low temperature for consistency
            )
            return llm
        except Exception as e:
            print(f"Warning: Failed to initialize LLM: {e}")
            return None
    
    def deterministic_fallback(self, message: str) -> str:
        """Provide deterministic response when LLM unavailable."""
        return f"[DETERMINISTIC MODE] {message}"
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent logic. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement execute()")
