"""
Improved ChatGPT Agent with standardized model architecture
"""
import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Type
import logging

from .models import BaseModel, ModelConfig, Message, AnthropicModel, OpenAIModel, GeminiModel
from .tools import BaseTool, CodeExecutionTool, WebSearchTool, WebContentTool, TerminalTool, MCPClient, BrowserMCPTool
from .utils.config import config

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class ChatGPTAgent:
    """Improved ChatGPT Agent with standardized architecture"""
    
    def __init__(self, 
                 model_provider: str = None,
                 model_name: str = None,
                 enable_logging: bool = None,
                 enable_mcp: bool = None):
        """
        Initialize the agent
        
        Args:
            model_provider: AI model provider (anthropic, openai, gemini)
            model_name: Specific model name
            enable_logging: Enable session logging
            enable_mcp: Enable MCP tools (browser automation, etc.)
        """
        self.model_provider = model_provider or config.DEFAULT_MODEL_PROVIDER
        self.model_name = model_name or config.DEFAULT_MODEL_NAME
        self.enable_logging = enable_logging if enable_logging is not None else config.ENABLE_LOGGING
        self.enable_mcp = enable_mcp if enable_mcp is not None else getattr(config, 'ENABLE_MCP', False)
        
        # Initialize model
        self.model = self._create_model()
        
        # Initialize MCP client
        self.mcp_client = MCPClient() if self.enable_mcp else None
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Session management
        self.session_id = None
        self.conversation_history = []
        self.session_log_dir = config.SESSION_LOG_DIR
        
        # Create log directory if logging is enabled
        if self.enable_logging:
            os.makedirs(self.session_log_dir, exist_ok=True)
    
    def _create_model(self) -> BaseModel:
        """Create model instance based on provider"""
        model_classes = {
            "anthropic": AnthropicModel,
            "openai": OpenAIModel,
            "gemini": GeminiModel
        }
        
        if self.model_provider not in model_classes:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")
        
        model_class = model_classes[self.model_provider]
        model_config = ModelConfig(**config.get_model_config(self.model_provider, self.model_name))
        
        return model_class(model_config)
    
    def _initialize_tools(self) -> Dict[str, BaseTool]:
        """Initialize available tools"""
        tools = {}
        
        # Add core tools
        tools["code_execution"] = CodeExecutionTool()
        tools["web_search"] = WebSearchTool()
        tools["web_content"] = WebContentTool()
        tools["terminal"] = TerminalTool()
        
        # Add MCP tools if enabled
        if self.enable_mcp and self.mcp_client:
            tools["browser_automation"] = BrowserMCPTool(self.mcp_client)
            logger.info("MCP browser automation tool enabled")
        
        return tools
    
    def add_tool(self, tool: BaseTool) -> None:
        """Add a custom tool to the agent"""
        self.tools[tool.name] = tool
        logger.info(f"Added tool: {tool.name}")
    
    def remove_tool(self, tool_name: str) -> None:
        """Remove a tool from the agent"""
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.info(f"Removed tool: {tool_name}")
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all available tools"""
        return [tool.get_schema() for tool in self.tools.values()]
    
    async def chat(self, message: str, session_id: str = None) -> str:
        """
        Chat with the agent
        
        Args:
            message: User message
            session_id: Optional session ID for conversation continuity
            
        Returns:
            Agent response
        """
        try:
            # Create or continue session
            if session_id:
                self.session_id = session_id
            elif not self.session_id:
                self.session_id = self._create_session()
            
            # Add user message to history
            user_msg = Message(role="user", content=message)
            self.conversation_history.append(user_msg)
            
            # Process conversation
            response = await self._process_conversation()
            
            # Log session if enabled
            if self.enable_logging:
                self._log_session()
            
            return response
            
        except Exception as e:
            logger.error(f"Chat processing failed: {str(e)}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    async def _process_conversation(self) -> str:
        """Process the conversation with tool execution loop"""
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Get model response
            tools_schemas = self.get_tool_schemas()
            response = await self.model.generate_response(
                self.conversation_history,
                tools_schemas if tools_schemas else None
            )
            
            # Add assistant response to history
            assistant_msg = Message(
                role="assistant",
                content=response.content,
                tool_calls=[{
                    "id": tc.id,
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.parameters)
                    }
                } for tc in response.tool_calls] if response.tool_calls else None
            )
            self.conversation_history.append(assistant_msg)
            
            # Execute tools if present
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_result = await self._execute_tool(tool_call)
                    
                    # Add tool result to history
                    tool_msg = Message(
                        role="tool",
                        content=tool_result.content,
                        tool_call_id=tool_call.id,
                        name=tool_call.name
                    )
                    self.conversation_history.append(tool_msg)
                
                # Continue conversation after tool execution
                continue
            
            # No tools called, return response
            return self._extract_final_response(response.content)
        
        return "Maximum conversation iterations reached."
    
    async def _execute_tool(self, tool_call) -> Any:
        """Execute a tool call"""
        tool_name = tool_call.name
        
        if tool_name not in self.tools:
            from .tools.base_tool import ToolResult
            return ToolResult(
                success=False,
                content="",
                error=f"Tool '{tool_name}' not found"
            )
        
        tool = self.tools[tool_name]
        
        try:
            # Validate parameters
            tool.validate_parameters(**tool_call.parameters)
            
            # Execute tool
            result = await tool.execute(**tool_call.parameters)
            
            logger.info(f"Tool '{tool_name}' executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Tool '{tool_name}' execution failed: {str(e)}")
            from .tools.base_tool import ToolResult
            return ToolResult(
                success=False,
                content="",
                error=f"Tool execution failed: {str(e)}"
            )
    
    def _extract_final_response(self, content: str) -> str:
        """Extract final response from content"""
        # Handle channel-based responses
        if "<final>" in content:
            parts = content.split("<final>")
            if len(parts) > 1:
                return parts[1].split("</final>")[0].strip()
        
        # Return full content if no channels
        return content.strip()
    
    def _create_session(self) -> str:
        """Create a new session ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"session_{timestamp}_{uuid.uuid4().hex[:8]}"
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    def _log_session(self) -> None:
        """Log session to file"""
        if not self.session_id:
            return
        
        log_data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "conversation_history": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "tool_calls": msg.tool_calls,
                    "tool_call_id": msg.tool_call_id,
                    "name": msg.name
                }
                for msg in self.conversation_history
            ]
        }
        
        log_file = os.path.join(self.session_log_dir, f"{self.session_id}.json")
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session information"""
        return {
            "session_id": self.session_id,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "conversation_length": len(self.conversation_history),
            "available_tools": list(self.tools.keys()),
            "model_info": self.model.get_model_info()
        }
    
    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "tool_calls": msg.tool_calls,
                "tool_call_id": msg.tool_call_id,
                "name": msg.name
            }
            for msg in self.conversation_history
        ]
    
    async def get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get available MCP tools"""
        if not self.enable_mcp or not self.mcp_client:
            return []
        
        return self.mcp_client.get_available_tools()
    
    async def connect_mcp_servers(self) -> Dict[str, bool]:
        """Connect to MCP servers"""
        if not self.enable_mcp or not self.mcp_client:
            return {}
        
        return await self.mcp_client.connect_all_servers()
    
    async def cleanup(self):
        """Clean up resources"""
        if self.mcp_client:
            await self.mcp_client.cleanup()
        
        # Clean up individual tools
        for tool in self.tools.values():
            if hasattr(tool, 'cleanup'):
                await tool.cleanup()
        
        logger.info("Agent cleanup completed")