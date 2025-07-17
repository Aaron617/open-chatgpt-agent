"""
OpenAI GPT model implementation
"""
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
import json

from .base_model import BaseModel, ModelConfig, Message, ToolCall, ModelResponse

class OpenAIModel(BaseModel):
    """OpenAI GPT model implementation"""
    
    def _initialize_client(self) -> None:
        """Initialize OpenAI client"""
        self.client = AsyncOpenAI(api_key=self.config.api_key)
    
    async def generate_response(
        self, 
        messages: List[Message], 
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> ModelResponse:
        """Generate response using OpenAI GPT"""
        cleaned_messages = self.clean_messages(messages)
        openai_messages = self._convert_messages(cleaned_messages)
        
        kwargs = {
            "model": self.config.model_name,
            "messages": openai_messages,
            "temperature": self.config.temperature,
            **self.config.additional_params
        }
        
        if self.config.max_tokens:
            kwargs["max_tokens"] = self.config.max_tokens
        
        if tools:
            kwargs["tools"] = self.format_tools(tools)
            kwargs["tool_choice"] = "auto"
        
        response = await self.client.chat.completions.create(**kwargs)
        return self._parse_response(response)
    
    def format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format tools for OpenAI API"""
        formatted_tools = []
        for tool in tools:
            formatted_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            }
            formatted_tools.append(formatted_tool)
        return formatted_tools
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert messages to OpenAI format"""
        openai_messages = []
        
        for msg in messages:
            openai_msg = {
                "role": msg.role,
                "content": msg.content
            }
            
            if msg.tool_calls:
                openai_msg["tool_calls"] = []
                for tool_call in msg.tool_calls:
                    openai_msg["tool_calls"].append({
                        "id": tool_call.get("id"),
                        "type": "function",
                        "function": {
                            "name": tool_call.get("function", {}).get("name"),
                            "arguments": tool_call.get("function", {}).get("arguments")
                        }
                    })
            
            if msg.tool_call_id:
                openai_msg["tool_call_id"] = msg.tool_call_id
            
            if msg.name:
                openai_msg["name"] = msg.name
            
            openai_messages.append(openai_msg)
        
        return openai_messages
    
    def _parse_response(self, response: Any) -> ModelResponse:
        """Parse OpenAI response to standardized format"""
        message = response.choices[0].message
        
        content = message.content or ""
        tool_calls = []
        
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_calls.append(ToolCall(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    parameters=json.loads(tool_call.function.arguments)
                ))
        
        usage = None
        if hasattr(response, 'usage') and response.usage:
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        
        return ModelResponse(
            content=content,
            tool_calls=tool_calls if tool_calls else None,
            usage=usage,
            model=response.model,
            finish_reason=response.choices[0].finish_reason
        )