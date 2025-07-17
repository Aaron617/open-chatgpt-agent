#!/usr/bin/env python3
"""
Browser MCP Tool usage example
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agent import ChatGPTAgent
from tools import MCPClient, MCPServerConfig, BrowserMCPTool
from utils.config import config

async def test_browser_mcp():
    """Test browser MCP tool functionality"""
    print("Browser MCP Tool - Usage Example")
    print("=" * 50)
    
    # Check MCP configuration
    if not config.ENABLE_MCP:
        print("MCP is disabled in configuration")
        print("Please set ENABLE_MCP=true in your .env file")
        return
    
    # Initialize MCP client
    mcp_client = MCPClient()
    
    # Configure browser server
    browser_config = MCPServerConfig(
        name="browser_use",
        command=config.MCP_BROWSER_COMMAND,
        args=config.MCP_BROWSER_ARGS.split(","),
        env=None,
        enabled=True
    )
    
    await mcp_client.add_server_config(browser_config)
    
    # Initialize browser tool
    browser_tool = BrowserMCPTool(mcp_client)
    
    print("Testing browser automation capabilities...")
    print("-" * 30)
    
    # Test 1: Navigate to a website
    print("\n1. Testing navigation...")
    try:
        result = await browser_tool.navigate("https://httpbin.org/html")
        print(f"Navigation result: {result.success}")
        if result.success:
            print(f"Content preview: {result.content[:200]}...")
        else:
            print(f"Error: {result.error}")
    except Exception as e:
        print(f"Navigation failed: {e}")
    
    # Test 2: Take a screenshot
    print("\n2. Testing screenshot...")
    try:
        result = await browser_tool.screenshot()
        print(f"Screenshot result: {result.success}")
        if result.success:
            print(f"Screenshot info: {result.content}")
        else:
            print(f"Error: {result.error}")
    except Exception as e:
        print(f"Screenshot failed: {e}")
    
    # Test 3: Get page content
    print("\n3. Testing page content extraction...")
    try:
        result = await browser_tool.get_page_content()
        print(f"Content extraction result: {result.success}")
        if result.success:
            print(f"Page content preview: {result.content[:300]}...")
        else:
            print(f"Error: {result.error}")
    except Exception as e:
        print(f"Content extraction failed: {e}")
    
    # Test 4: Try to find an element
    print("\n4. Testing element finding...")
    try:
        result = await browser_tool.execute("find_element", selector="body")
        print(f"Element finding result: {result.success}")
        if result.success:
            print(f"Element info: {result.content}")
        else:
            print(f"Error: {result.error}")
    except Exception as e:
        print(f"Element finding failed: {e}")
    
    # Cleanup
    await browser_tool.cleanup()
    print("\nBrowser tool cleanup completed")

async def test_agent_with_browser():
    """Test agent with browser MCP tool"""
    print("\n" + "=" * 50)
    print("Agent with Browser MCP Tool")
    print("=" * 50)
    
    # Check configuration
    if not config.ANTHROPIC_API_KEY:
        print("Anthropic API key not configured")
        print("Please set ANTHROPIC_API_KEY in your .env file")
        return
    
    # Initialize agent with MCP enabled
    agent = ChatGPTAgent(
        model_provider="anthropic",
        enable_mcp=True
    )
    
    # Connect to MCP servers
    print("Connecting to MCP servers...")
    connections = await agent.connect_mcp_servers()
    print(f"MCP connections: {connections}")
    
    # Get available tools
    session_info = agent.get_session_info()
    print(f"Available tools: {session_info['available_tools']}")
    
    # Test browser automation through agent
    browser_queries = [
        "Navigate to https://httpbin.org/html and take a screenshot",
        "Get the content of the current page",
        "Find all the links on the page"
    ]
    
    for i, query in enumerate(browser_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 40)
        
        try:
            response = await agent.chat(query)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Small delay between requests
        await asyncio.sleep(2)
    
    # Cleanup
    await agent.cleanup()
    print("\nAgent cleanup completed")

async def main():
    """Main function to run all tests"""
    print("Starting Browser MCP Tool Tests...")
    
    # Test 1: Direct browser tool usage
    await test_browser_mcp()
    
    # Test 2: Agent with browser tool
    await test_agent_with_browser()
    
    print("\n" + "=" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())