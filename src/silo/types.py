from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field

class AgentResponse(BaseModel):
    """
    Standard response format for SILO skills.
    
    Attributes:
        llm_text: The summarized/truncated text intended for the LLM.
        raw_data: Full raw JSON data for the orchestrator (can be used for UI widgets, etc.).
        status: Status of the execution ('success' or 'error').
        error_message: Optional error message if status is 'error'.
    """
    llm_text: str
    raw_data: Optional[Dict[str, Any]] = None
    status: str = "success"
    error_message: Optional[str] = None

    def to_json(self) -> str:
        return self.model_dump_json()
