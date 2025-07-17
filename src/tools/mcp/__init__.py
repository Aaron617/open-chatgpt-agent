"""
MCP (Model Context Protocol) client package
"""
from .mcp_client import MCPClient, MCPServerConfig, MCPTool, DEFAULT_SERVER_CONFIGS
from .browser_mcp_tool import BrowserMCPTool

__all__ = [
    "MCPClient",
    "MCPServerConfig", 
    "MCPTool",
    "DEFAULT_SERVER_CONFIGS",
    "BrowserMCPTool"
]