"""
Web search tool using Exa API
"""
import asyncio
import aiohttp
from typing import List, Dict, Any
from .base_tool import BaseTool, ToolResult
from ..utils.config import config

class WebSearchTool(BaseTool):
    """Tool for searching the web using Exa API"""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for information and return relevant results"
        )
        self.api_key = config.EXA_API_KEY
        self.base_url = "https://api.exa.ai/search"
        self.filter_keywords = ['gaia', 'huggingface']  # Keywords to filter out
    
    async def execute(self, query: str, topn: int = 10) -> ToolResult:
        """Search the web and return results"""
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
                "query": query,
                "num_results": topn,
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
                            error=f"Search API error: {response.status} - {error_text}"
                        )
                    
                    data = await response.json()
                    results = self._process_results(data.get("results", []))
                    
                    return ToolResult(
                        success=True,
                        content=self._format_results(results),
                        metadata={
                            "query": query,
                            "total_results": len(results),
                            "filtered_results": len(results)
                        }
                    )
                    
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Web search failed: {str(e)}"
            )
    
    def _process_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and filter search results"""
        processed = []
        
        for result in results:
            # Filter out unwanted results
            if any(keyword in result.get("url", "").lower() for keyword in self.filter_keywords):
                continue
            
            processed_result = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("text", "")[:500] + "..." if len(result.get("text", "")) > 500 else result.get("text", ""),
                "published_date": result.get("publishedDate", ""),
                "score": result.get("score", 0)
            }
            
            processed.append(processed_result)
        
        return processed
    
    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for display"""
        if not results:
            return "No search results found."
        
        formatted = "Search Results:\n" + "=" * 50 + "\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"{i}. {result['title']}\n"
            formatted += f"   URL: {result['url']}\n"
            formatted += f"   Snippet: {result['snippet']}\n"
            if result['published_date']:
                formatted += f"   Published: {result['published_date']}\n"
            formatted += f"   Score: {result['score']}\n"
            formatted += "\n"
        
        return formatted