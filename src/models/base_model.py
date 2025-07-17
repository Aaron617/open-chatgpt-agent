"""
Base model class for AI provider abstraction
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator, Union
from dataclasses import dataclass
import json

@dataclass
class ModelConfig:
    """Configuration for AI model"""
    model_name: str
    api_key: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 60
    additional_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}

@dataclass
class Message:
    """Standardized message format"""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

@dataclass
class ToolCall:
    """Standardized tool call format"""
    id: str
    name: str
    parameters: Dict[str, Any]

@dataclass
class ModelResponse:
    """Standardized model response format"""
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None

class BaseModel(ABC):
    """Abstract base class for AI model providers"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.client = None
        self._initialize_client()
    
    @abstractmethod
    def _initialize_client(self) -> None:
        """Initialize the provider-specific client"""
        pass
    
    @abstractmethod
    async def generate_response(
        self, 
        messages: List[Message], 
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> ModelResponse:
        """Generate a response from the model"""
        pass
    
    @abstractmethod
    def format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format tools for the specific provider"""
        pass
    
    @abstractmethod
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert standardized messages to provider-specific format"""
        pass
    
    @abstractmethod
    def _parse_response(self, response: Any) -> ModelResponse:
        """Parse provider-specific response to standardized format"""
        pass
    
    def clean_messages(self, messages: List[Message]) -> List[Message]:
        """Clean messages by removing trailing whitespace"""
        cleaned = []
        for msg in messages:
            cleaned_msg = Message(
                role=msg.role,
                content=msg.content.rstrip() if msg.content else "",
                tool_calls=msg.tool_calls,
                tool_call_id=msg.tool_call_id,
                name=msg.name
            )
            cleaned.append(cleaned_msg)
        return cleaned
    
    def validate_config(self) -> bool:
        """Validate model configuration"""
        if not self.config.model_name:
            raise ValueError("Model name is required")
        if not self.config.api_key:
            raise ValueError("API key is required")
        return True
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model"""
        return {
            "model_name": self.config.model_name,
            "provider": self.__class__.__name__,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }