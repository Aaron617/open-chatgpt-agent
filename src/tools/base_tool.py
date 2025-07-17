"""
Base tool class for agent tools
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import inspect

@dataclass
class ToolParameter:
    """Tool parameter definition"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None

@dataclass
class ToolResult:
    """Tool execution result"""
    success: bool
    content: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseTool(ABC):
    """Abstract base class for agent tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.parameters = self._extract_parameters()
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        pass
    
    def _extract_parameters(self) -> List[ToolParameter]:
        """Extract parameters from the execute method signature"""
        sig = inspect.signature(self.execute)
        parameters = []
        
        for param_name, param in sig.parameters.items():
            if param_name == "kwargs":
                continue
                
            param_type = "string"
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == list:
                    param_type = "array"
                elif param.annotation == dict:
                    param_type = "object"
            
            required = param.default == inspect.Parameter.empty
            default = param.default if param.default != inspect.Parameter.empty else None
            
            parameters.append(ToolParameter(
                name=param_name,
                type=param_type,
                description=f"Parameter {param_name}",
                required=required,
                default=default
            ))
        
        return parameters
    
    def get_schema(self) -> Dict[str, Any]:
        """Get OpenAPI-style schema for the tool"""
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description
            }
            
            if param.default is not None:
                properties[param.name]["default"] = param.default
            
            if param.required:
                required.append(param.name)
        
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    
    def validate_parameters(self, **kwargs) -> bool:
        """Validate tool parameters"""
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                raise ValueError(f"Required parameter '{param.name}' is missing")
        
        return True