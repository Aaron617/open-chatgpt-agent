"""
Anthropic Claude model implementation
"""
from typing import Dict, List, Any, Optional
from anthropic import AsyncAnthropic
import json

from .base_model import BaseModel, ModelConfig, Message, ToolCall, ModelResponse

class AnthropicModel(BaseModel):
    """Anthropic Claude model implementation"""
    
    def _initialize_client(self) -> None:
        """Initialize Anthropic client"""
        self.client = AsyncAnthropic(api_key=self.config.api_key)
    
    async def generate_response(
        self, 
        messages: List[Message], 
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> ModelResponse:
        """Generate response using Anthropic Claude"""
        cleaned_messages = self.clean_messages(messages)
        anthropic_messages = self._convert_messages(cleaned_messages)
        
        kwargs = {
            "model": self.config.model_name,
            "messages": anthropic_messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens or 4096,
            **self.config.additional_params
        }
        
        if tools:
            kwargs["tools"] = self.format_tools(tools)
        
        response = await self.client.messages.create(**kwargs)
        return self._parse_response(response)
    
    def format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format tools for Anthropic API"""
        formatted_tools = []
        for tool in tools:
            formatted_tool = {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"]
            }
            formatted_tools.append(formatted_tool)
        return formatted_tools
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert messages to Anthropic format"""
        anthropic_messages = []
        
        for msg in messages:
            if msg.role == "system":
                # Anthropic handles system messages differently
                continue
                
            anthropic_msg = {
                "role": msg.role,
                "content": []
            }
            
            if msg.content:
                anthropic_msg["content"].append({
                    "type": "text",
                    "text": msg.content
                })
            
            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    anthropic_msg["content"].append({
                        "type": "tool_use",
                        "id": tool_call.get("id"),
                        "name": tool_call.get("function", {}).get("name"),
                        "input": json.loads(tool_call.get("function", {}).get("arguments", "{}"))
                    })
            
            if msg.tool_call_id:
                anthropic_msg["content"].append({
                    "type": "tool_result",
                    "tool_use_id": msg.tool_call_id,
                    "content": msg.content
                })
            
            anthropic_messages.append(anthropic_msg)
        
        return anthropic_messages
    
    def _parse_response(self, response: Any) -> ModelResponse:
        """Parse Anthropic response to standardized format"""
        content = ""
        tool_calls = []
        
        for content_block in response.content:
            if content_block.type == "text":
                content += content_block.text
            elif content_block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=content_block.id,
                    name=content_block.name,
                    parameters=content_block.input
                ))
        
        usage = None
        if hasattr(response, 'usage'):
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
        
        return ModelResponse(
            content=content,
            tool_calls=tool_calls if tool_calls else None,
            usage=usage,
            model=response.model,
            finish_reason=response.stop_reason
        )