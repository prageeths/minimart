"""Base agent class for all agents in the system."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import json
import logging
from app.models.models import AgentType, AgentLog, AgentInteraction
from app.database.database import SessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.logger = logging.getLogger(f"agent.{agent_type.value}")
        
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's main functionality."""
        pass
    
    async def log_action(
        self, 
        action: str, 
        input_data: Dict[str, Any], 
        output_data: Dict[str, Any],
        status: str = "success",
        error_message: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ) -> int:
        """Log agent action to database."""
        db = SessionLocal()
        try:
            log_entry = AgentLog(
                agent_type=self.agent_type,
                action=action,
                input_data=json.dumps(input_data),
                output_data=json.dumps(output_data),
                status=status,
                error_message=error_message,
                execution_time_ms=execution_time_ms
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            return log_entry.id
        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to log action: {e}")
            raise
        finally:
            db.close()
    
    async def log_interaction(
        self,
        to_agent: AgentType,
        interaction_type: str,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        log_id: Optional[int] = None
    ) -> int:
        """Log agent-to-agent interaction."""
        db = SessionLocal()
        try:
            interaction = AgentInteraction(
                from_agent=self.agent_type,
                to_agent=to_agent,
                interaction_type=interaction_type,
                message=message,
                data=json.dumps(data) if data else None,
                log_id=log_id
            )
            db.add(interaction)
            db.commit()
            db.refresh(interaction)
            return interaction.id
        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to log interaction: {e}")
            raise
        finally:
            db.close()
    
    async def send_message(
        self, 
        to_agent: AgentType, 
        message: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> int:
        """Send a message to another agent."""
        return await self.log_interaction(
            to_agent=to_agent,
            interaction_type="message",
            message=message,
            data=data
        )
    
    async def send_request(
        self, 
        to_agent: AgentType, 
        request_data: Dict[str, Any]
    ) -> int:
        """Send a request to another agent."""
        return await self.log_interaction(
            to_agent=to_agent,
            interaction_type="request",
            data=request_data
        )
    
    async def send_response(
        self, 
        to_agent: AgentType, 
        response_data: Dict[str, Any],
        log_id: Optional[int] = None
    ) -> int:
        """Send a response to another agent."""
        return await self.log_interaction(
            to_agent=to_agent,
            interaction_type="response",
            data=response_data,
            log_id=log_id
        )
    
    def validate_input(self, input_data: Dict[str, Any], required_fields: list) -> bool:
        """Validate input data has required fields."""
        for field in required_fields:
            if field not in input_data:
                self.logger.error(f"Missing required field: {field}")
                return False
        return True
    
    def create_error_response(self, error_message: str, error_code: Optional[str] = None) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "success": False,
            "error": error_message,
            "error_code": error_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def create_success_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create standardized success response."""
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
