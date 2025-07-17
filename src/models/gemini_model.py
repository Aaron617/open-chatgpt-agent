"""
Google Gemini model implementation
"""
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Schema
import json

from .base_model import BaseModel, ModelConfig, Message, ToolCall, ModelResponse

class GeminiModel(BaseModel):
    """Google Gemini model implementation"""
    
    def _initialize_client(self) -> None:
        """Initialize Gemini client"""
        genai.configure(api_key=self.config.api_key)
        self.client = genai.GenerativeModel(self.config.model_name)
    
    async def generate_response(
        self, 
        messages: List[Message], 
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> ModelResponse:
        """Generate response using Google Gemini"""
        cleaned_messages = self.clean_messages(messages)
        gemini_messages = self._convert_messages(cleaned_messages)
        
        kwargs = {
            "generation_config": genai.types.GenerationConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
                **self.config.additional_params
            )
        }
        
        if tools:
            kwargs["tools"] = self.format_tools(tools)
        
        # Start chat with history
        chat = self.client.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])
        
        # Send last message
        last_message = gemini_messages[-1]["parts"][0] if gemini_messages else ""
        response = await chat.send_message_async(last_message, **kwargs)
        
        return self._parse_response(response)
    
    def format_tools(self, tools: List[Dict[str, Any]]) -> List[FunctionDeclaration]:
        """Format tools for Gemini API"""
        formatted_tools = []
        for tool in tools:
            # Convert input_schema to Gemini Schema format
            schema = self._convert_schema(tool["input_schema"])
            
            func_declaration = FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=schema
            )
            formatted_tools.append(func_declaration)
        return formatted_tools
    
    def _convert_schema(self, input_schema: Dict[str, Any]) -> Schema:
        """Convert JSON schema to Gemini Schema"""
        return Schema(
            type_=input_schema.get("type", "object"),
            properties={
                key: Schema(
                    type_=value.get("type", "string"),
                    description=value.get("description", "")
                )
                for key, value in input_schema.get("properties", {}).items()
            },
            required=input_schema.get("required", [])
        )
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert messages to Gemini format"""
        gemini_messages = []
        
        for msg in messages:
            # Map roles to Gemini format
            role = "user" if msg.role in ["user", "system"] else "model"
            
            gemini_msg = {
                "role": role,
                "parts": []
            }
            
            if msg.content:
                gemini_msg["parts"].append(msg.content)
            
            # Handle tool calls and results
            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    gemini_msg["parts"].append({
                        "function_call": {
                            "name": tool_call.get("function", {}).get("name"),
                            "args": json.loads(tool_call.get("function", {}).get("arguments", "{}"))
                        }
                    })
            
            if msg.tool_call_id:
                gemini_msg["parts"].append({
                    "function_response": {
                        "name": msg.name or "function",
                        "response": {"result": msg.content}
                    }
                })
            
            gemini_messages.append(gemini_msg)
        
        return gemini_messages
    
    def _parse_response(self, response: Any) -> ModelResponse:
        """Parse Gemini response to standardized format"""
        content = ""
        tool_calls = []
        
        for part in response.parts:
            if hasattr(part, 'text'):
                content += part.text
            elif hasattr(part, 'function_call'):
                tool_calls.append(ToolCall(
                    id=f"call_{hash(part.function_call.name)}",
                    name=part.function_call.name,
                    parameters=dict(part.function_call.args)
                ))
        
        usage = None
        if hasattr(response, 'usage_metadata'):
            usage = {
                "input_tokens": response.usage_metadata.prompt_token_count,
                "output_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count
            }
        
        return ModelResponse(
            content=content,
            tool_calls=tool_calls if tool_calls else None,
            usage=usage,
            model=self.config.model_name,
            finish_reason=response.candidates[0].finish_reason.name if response.candidates else None
        )