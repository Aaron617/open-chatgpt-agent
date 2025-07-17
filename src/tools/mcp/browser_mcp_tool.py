"""
Browser MCP Tool implementation
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from ..base_tool import BaseTool, ToolResult
from .mcp_client import MCPClient, MCPServerConfig

logger = logging.getLogger(__name__)

class BrowserMCPTool(BaseTool):
    """Browser tool using MCP server for browser automation"""
    
    def __init__(self, mcp_client: MCPClient = None):
        super().__init__(
            name="browser_automation",
            description="Browser automation tool using MCP server for web navigation, screenshots, clicking, typing, and more"
        )
        self.mcp_client = mcp_client or MCPClient()
        self.server_name = "browser_use"
        self.connected = False
        
    async def _ensure_connected(self):
        """Ensure browser MCP server is connected"""
        if not self.connected:
            await self._setup_browser_server()
    
    async def _setup_browser_server(self):
        """Setup browser MCP server connection"""
        try:
            # Configure browser server based on available options
            browser_configs = [
                # Browser-use server (if available)
                MCPServerConfig(
                    name="browser_use",
                    command="npx",
                    args=["@co-browser/browser-use-mcp"],
                    env=None,
                    enabled=True
                ),
                # Puppeteer server as fallback
                MCPServerConfig(
                    name="puppeteer",
                    command="npx",
                    args=["@modelcontextprotocol/server-puppeteer"],
                    env=None,
                    enabled=True
                ),
                # Playwright server as another fallback
                MCPServerConfig(
                    name="playwright",
                    command="node",
                    args=["playwright-server.js"],
                    env=None,
                    enabled=True
                )
            ]
            
            # Try to connect to available browser servers
            for config in browser_configs:
                await self.mcp_client.add_server_config(config)
                if await self.mcp_client.connect_to_server(config.name):
                    self.server_name = config.name
                    self.connected = True
                    logger.info(f"Connected to browser server: {config.name}")
                    break
            
            if not self.connected:
                logger.warning("No browser MCP server could be connected")
                
        except Exception as e:
            logger.error(f"Failed to setup browser server: {str(e)}")
            raise
    
    async def execute(self, 
                     action: str,
                     url: Optional[str] = None,
                     selector: Optional[str] = None,
                     text: Optional[str] = None,
                     wait_for: Optional[str] = None,
                     **kwargs) -> ToolResult:
        """
        Execute browser automation action
        
        Args:
            action: Browser action to perform (navigate, click, type, screenshot, etc.)
            url: URL to navigate to
            selector: CSS selector for element interaction
            text: Text to type
            wait_for: Wait for element or condition
            **kwargs: Additional parameters
        """
        try:
            await self._ensure_connected()
            
            if not self.connected:
                return ToolResult(
                    success=False,
                    content="",
                    error="Browser MCP server not available"
                )
            
            # Map action to appropriate MCP tool call
            tool_name, arguments = self._map_action_to_tool(
                action, url, selector, text, wait_for, **kwargs
            )
            
            # Call the MCP tool
            result = await self.mcp_client.call_tool(tool_name, arguments)
            
            # Format the result
            content = self._format_result(result)
            
            return ToolResult(
                success=True,
                content=content,
                metadata={
                    "action": action,
                    "server": self.server_name,
                    "tool": tool_name
                }
            )
            
        except Exception as e:
            logger.error(f"Browser action '{action}' failed: {str(e)}")
            return ToolResult(
                success=False,
                content="",
                error=f"Browser action failed: {str(e)}"
            )
    
    def _map_action_to_tool(self, action: str, url: str, selector: str, 
                           text: str, wait_for: str, **kwargs) -> tuple:
        """Map browser action to MCP tool name and arguments"""
        
        # Standard browser actions mapping
        action_mappings = {
            "navigate": self._navigate_args,
            "click": self._click_args,
            "type": self._type_args,
            "screenshot": self._screenshot_args,
            "wait": self._wait_args,
            "get_page_content": self._get_content_args,
            "find_element": self._find_element_args,
            "scroll": self._scroll_args,
            "back": self._back_args,
            "forward": self._forward_args,
            "refresh": self._refresh_args,
            "close": self._close_args
        }
        
        if action not in action_mappings:
            raise ValueError(f"Unknown browser action: {action}")
        
        return action_mappings[action](url, selector, text, wait_for, **kwargs)
    
    def _navigate_args(self, url: str, selector: str, text: str, wait_for: str, **kwargs):
        """Generate arguments for navigate action"""
        tool_name = f"{self.server_name}_navigate"
        arguments = {"url": url}
        if wait_for:
            arguments["waitFor"] = wait_for
        return tool_name, arguments
    
    def _click_args(self, url: str, selector: str, text: str, wait_for: str, **kwargs):
        """Generate arguments for click action"""
        tool_name = f"{self.server_name}_click"
        arguments = {"selector": selector}
        if wait_for:
            arguments["waitFor"] = wait_for
        return tool_name, arguments
    
    def _type_args(self, url: str, selector: str, text: str, wait_for: str, **kwargs):
        """Generate arguments for type action"""
        tool_name = f"{self.server_name}_type"
        arguments = {"selector": selector, "text": text}
        return tool_name, arguments
    
    def _screenshot_args(self, url: str, selector: str, text: str, wait_for: str, **kwargs):
        """Generate arguments for screenshot action"""
        tool_name = f"{self.server_name}_screenshot"
        arguments = {}
        if selector:
            arguments["selector"] = selector
        if kwargs.get("fullPage"):
            arguments["fullPage"] = True
        return tool_name, arguments
    
    def _wait_args(self, url: str, selector: str, text: str, wait_for: str, **kwargs):
        """Generate arguments for wait action"""
        tool_name = f"{self.server_name}_wait"
        arguments = {"selector": wait_for or selector}
        if kwargs.get("timeout"):
            arguments["timeout"] = kwargs["timeout"]
        return tool_name, arguments
    
    def _get_content_args(self, url: str, selector: str, text: str, wait_for: str, **kwargs):
        """Generate arguments for get page content action"""
        tool_name = f"{self.server_name}_get_page_content"
        arguments = {}
        if selector:
            arguments["selector"] = selector
        return tool_name, arguments
    
    def _find_element_args(self, url: str, selector: str, text: str, wait_for: str, **kwargs):
        """Generate arguments for find element action"""
        tool_name = f"{self.server_name}_find_element"
        arguments = {"selector": selector}
        return tool_name, arguments
    
    def _scroll_args(self, url: str, selector: str, text: str, wait_for: str, **kwargs):
        """Generate arguments for scroll action"""
        tool_name = f"{self.server_name}_scroll"
        arguments = {}
        if selector:
            arguments["selector"] = selector
        if kwargs.get("direction"):
            arguments["direction"] = kwargs["direction"]
        if kwargs.get("amount"):
            arguments["amount"] = kwargs["amount"]
        return tool_name, arguments
    
    def _back_args(self, url: str, selector: str, text: str, wait_for: str, **kwargs):
        """Generate arguments for back action"""
        tool_name = f"{self.server_name}_back"
        return tool_name, {}
    
    def _forward_args(self, url: str, selector: str, text: str, wait_for: str, **kwargs):
        """Generate arguments for forward action"""
        tool_name = f"{self.server_name}_forward"
        return tool_name, {}
    
    def _refresh_args(self, url: str, selector: str, text: str, wait_for: str, **kwargs):
        """Generate arguments for refresh action"""
        tool_name = f"{self.server_name}_refresh"
        return tool_name, {}
    
    def _close_args(self, url: str, selector: str, text: str, wait_for: str, **kwargs):
        """Generate arguments for close action"""
        tool_name = f"{self.server_name}_close"
        return tool_name, {}
    
    def _format_result(self, result: Any) -> str:
        """Format MCP tool result for display"""
        if hasattr(result, 'content'):
            content = result.content
            if isinstance(content, list):
                formatted_content = []
                for item in content:
                    if hasattr(item, 'text'):
                        formatted_content.append(item.text)
                    elif hasattr(item, 'type') and item.type == 'image':
                        formatted_content.append(f"[Image: {item.data if hasattr(item, 'data') else 'Screenshot captured'}]")
                    else:
                        formatted_content.append(str(item))
                return "\n".join(formatted_content)
            return str(content)
        return str(result)
    
    async def navigate(self, url: str, wait_for: str = None) -> ToolResult:
        """Navigate to a URL"""
        return await self.execute("navigate", url=url, wait_for=wait_for)
    
    async def click(self, selector: str, wait_for: str = None) -> ToolResult:
        """Click on an element"""
        return await self.execute("click", selector=selector, wait_for=wait_for)
    
    async def type_text(self, selector: str, text: str) -> ToolResult:
        """Type text into an element"""
        return await self.execute("type", selector=selector, text=text)
    
    async def screenshot(self, selector: str = None, full_page: bool = False) -> ToolResult:
        """Take a screenshot"""
        return await self.execute("screenshot", selector=selector, fullPage=full_page)
    
    async def wait_for_element(self, selector: str, timeout: int = 30000) -> ToolResult:
        """Wait for an element to appear"""
        return await self.execute("wait", wait_for=selector, timeout=timeout)
    
    async def get_page_content(self, selector: str = None) -> ToolResult:
        """Get page content"""
        return await self.execute("get_page_content", selector=selector)
    
    def get_available_actions(self) -> List[str]:
        """Get list of available browser actions"""
        return [
            "navigate", "click", "type", "screenshot", "wait",
            "get_page_content", "find_element", "scroll",
            "back", "forward", "refresh", "close"
        ]
    
    async def cleanup(self):
        """Clean up browser resources"""
        if self.mcp_client:
            await self.mcp_client.cleanup()