"""
Unified MCP Client for connecting to various MCP servers
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union
from contextlib import AsyncExitStack
from dataclasses import dataclass

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from ...utils.config import config

logger = logging.getLogger(__name__)

@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None
    enabled: bool = True

@dataclass
class MCPTool:
    """Represents an MCP tool"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str

class MCPClient:
    """Unified MCP client for connecting to multiple MCP servers"""
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self.tools: Dict[str, MCPTool] = {}
        self.server_configs: Dict[str, MCPServerConfig] = {}
        
    async def add_server_config(self, server_config: MCPServerConfig):
        """Add a server configuration"""
        self.server_configs[server_config.name] = server_config
        
    async def connect_to_server(self, server_name: str) -> bool:
        """Connect to a specific MCP server"""
        if server_name not in self.server_configs:
            logger.error(f"Server config not found: {server_name}")
            return False
            
        server_config = self.server_configs[server_name]
        
        if not server_config.enabled:
            logger.info(f"Server {server_name} is disabled")
            return False
            
        try:
            server_params = StdioServerParameters(
                command=server_config.command,
                args=server_config.args,
                env=server_config.env
            )
            
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )
            await session.initialize()
            
            # List available tools
            response = await session.list_tools()
            server_tools = []
            
            for tool in response.tools:
                tool_name = f"{server_name}_{tool.name}"
                mcp_tool = MCPTool(
                    name=tool_name,
                    description=tool.description,
                    input_schema=tool.inputSchema,
                    server_name=server_name
                )
                self.tools[tool_name] = mcp_tool
                server_tools.append(tool.name)
            
            self.sessions[server_name] = session
            logger.info(f"Connected to server '{server_name}' with tools: {server_tools}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to server '{server_name}': {str(e)}")
            return False
    
    async def connect_all_servers(self) -> Dict[str, bool]:
        """Connect to all configured servers"""
        results = {}
        for server_name in self.server_configs:
            results[server_name] = await self.connect_to_server(server_name)
        return results
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the appropriate server"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool = self.tools[tool_name]
        server_name = tool.server_name
        
        if server_name not in self.sessions:
            raise ValueError(f"Server '{server_name}' not connected")
        
        session = self.sessions[server_name]
        
        # Extract the actual tool name (remove server prefix)
        actual_tool_name = tool_name.split('_', 1)[1]
        
        try:
            result = await session.call_tool(actual_tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Tool call failed for '{tool_name}': {str(e)}")
            raise
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools in the format expected by AI models"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            for tool in self.tools.values()
        ]
    
    def get_tools_by_server(self, server_name: str) -> List[MCPTool]:
        """Get tools for a specific server"""
        return [
            tool for tool in self.tools.values()
            if tool.server_name == server_name
        ]
    
    async def list_server_tools(self, server_name: str) -> List[str]:
        """List tools available on a specific server"""
        if server_name not in self.sessions:
            return []
        
        session = self.sessions[server_name]
        response = await session.list_tools()
        return [tool.name for tool in response.tools]
    
    def is_server_connected(self, server_name: str) -> bool:
        """Check if a server is connected"""
        return server_name in self.sessions
    
    def get_connected_servers(self) -> List[str]:
        """Get list of connected servers"""
        return list(self.sessions.keys())
    
    async def disconnect_server(self, server_name: str):
        """Disconnect from a specific server"""
        if server_name in self.sessions:
            # Remove tools for this server
            tools_to_remove = [
                tool_name for tool_name, tool in self.tools.items()
                if tool.server_name == server_name
            ]
            for tool_name in tools_to_remove:
                del self.tools[tool_name]
            
            # Remove session
            del self.sessions[server_name]
            logger.info(f"Disconnected from server '{server_name}'")
    
    async def cleanup(self):
        """Clean up all resources"""
        await self.exit_stack.aclose()
        self.sessions.clear()
        self.tools.clear()
        logger.info("MCP client cleaned up")

# Default server configurations
DEFAULT_SERVER_CONFIGS = {
    "browser_use": MCPServerConfig(
        name="browser_use",
        command="npx",
        args=["@modelcontextprotocol/server-brave-search"],
        env=None,
        enabled=False  # Disabled by default, enable via config
    ),
    "puppeteer": MCPServerConfig(
        name="puppeteer",
        command="npx",
        args=["@modelcontextprotocol/server-puppeteer"],
        env=None,
        enabled=False
    ),
    "playwright": MCPServerConfig(
        name="playwright",
        command="node",
        args=["playwright-mcp-server.js"],
        env=None,
        enabled=False
    )
}