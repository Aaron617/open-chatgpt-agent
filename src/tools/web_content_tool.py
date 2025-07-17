"""
Web content fetching tool using Exa API
"""
import asyncio
import aiohttp
from .base_tool import BaseTool, ToolResult
from ..utils.config import config

class WebContentTool(BaseTool):
    """Tool for fetching full content from specific URLs"""
    
    def __init__(self):
        super().__init__(
            name="web_content",
            description="Fetch full content from a specific URL"
        )
        self.api_key = config.EXA_API_KEY
        self.base_url = "https://api.exa.ai/contents"
    
    async def execute(self, url: str) -> ToolResult:
        """Fetch content from a URL"""
        try:
            if not self.api_key:
                return ToolResult(
                    success=False,
                    content="",
                    error="Exa API key not configured"
                )
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "ids": [url],
                "text": True,
                "highlights": True,
                "summary": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return ToolResult(
                            success=False,
                            content="",
                            error=f"Content fetch API error: {response.status} - {error_text}"
                        )
                    
                    data = await response.json()
                    results = data.get("results", [])
                    
                    if not results:
                        return ToolResult(
                            success=False,
                            content="",
                            error="No content found for the provided URL"
                        )
                    
                    content = self._format_content(results[0])
                    
                    return ToolResult(
                        success=True,
                        content=content,
                        metadata={
                            "url": url,
                            "content_length": len(content),
                            "title": results[0].get("title", "")
                        }
                    )
                    
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Content fetch failed: {str(e)}"
            )
    
    def _format_content(self, result: dict) -> str:
        """Format content for display"""
        title = result.get("title", "")
        url = result.get("url", "")
        text = result.get("text", "")
        published_date = result.get("publishedDate", "")
        
        formatted = f"Title: {title}\n"
        formatted += f"URL: {url}\n"
        if published_date:
            formatted += f"Published: {published_date}\n"
        formatted += "\n" + "=" * 50 + "\n\n"
        formatted += text
        
        return formatted