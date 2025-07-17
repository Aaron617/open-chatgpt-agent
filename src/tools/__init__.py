"""
Tools package for the agent
"""
from .base_tool import BaseTool, ToolResult, ToolParameter
from .code_execution_tool import CodeExecutionTool
from .web_search_tool import WebSearchTool
from .web_content_tool import WebContentTool
from .terminal_tool import TerminalTool

# MCP (Model Context Protocol) tools
from .mcp.mcp_client import MCPClient, MCPServerConfig, MCPTool, DEFAULT_SERVER_CONFIGS
from .mcp.browser_mcp_tool import BrowserMCPTool

__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolParameter",
    "CodeExecutionTool",
    "WebSearchTool",
    "WebContentTool",
    "TerminalTool",
    # MCP tools
    "MCPClient",
    "MCPServerConfig",
    "MCPTool",
    "DEFAULT_SERVER_CONFIGS",
    "BrowserMCPTool"
]