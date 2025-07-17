#!/usr/bin/env python3
"""
Main entry point for the Open ChatGPT Agent
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agent import ChatGPTAgent
from utils.config import config

async def main():
    """Main function to run the agent"""
    print("🤖 Open ChatGPT Agent")
    print("=" * 50)
    
    # Check configuration
    print("Configuration Status:")
    try:
        config.print_config_status()
    except Exception as e:
        print(f"Configuration error: {e}")
        print("Please check your .env file and API keys")
        return
    
    # Check for missing keys
    missing_keys = config.get_missing_keys()
    if missing_keys:
        print(f"\n❌ Missing API keys: {', '.join(missing_keys)}")
        print("Please set these in your .env file")
        return
    
    print("\n✅ Configuration looks good!")
    
    # Initialize agent
    print("\n🚀 Initializing agent...")
    try:
        agent = ChatGPTAgent(
            model_provider=config.DEFAULT_MODEL_PROVIDER,
            enable_mcp=getattr(config, 'ENABLE_MCP', False)
        )
        
        # Connect to MCP servers if enabled
        if getattr(config, 'ENABLE_MCP', False):
            print("🔗 Connecting to MCP servers...")
            connections = await agent.connect_mcp_servers()
            if connections:
                print(f"Connected to: {list(connections.keys())}")
        
        # Get session info
        session_info = agent.get_session_info()
        print(f"📊 Session ID: {session_info['session_id']}")
        print(f"🛠️  Available tools: {', '.join(session_info['available_tools'])}")
        
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    # Interactive chat loop
    print("\n💬 Starting chat (type 'quit' to exit, 'help' for commands)")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() == 'quit':
                print("👋 Goodbye!")
                break
                
            if user_input.lower() == 'help':
                print("""
Available commands:
- quit: Exit the program
- help: Show this help message
- clear: Clear conversation history
- info: Show session information
- tools: List available tools

Or just chat normally with the agent!
                """)
                continue
                
            if user_input.lower() == 'clear':
                agent.clear_history()
                print("🗑️  Conversation history cleared")
                continue
                
            if user_input.lower() == 'info':
                info = agent.get_session_info()
                print(f"📊 Session: {info['session_id']}")
                print(f"🤖 Model: {info['model_info']['model_name']}")
                print(f"💬 Messages: {info['conversation_length']}")
                print(f"🛠️  Tools: {', '.join(info['available_tools'])}")
                continue
                
            if user_input.lower() == 'tools':
                tools = agent.get_session_info()['available_tools']
                print("🛠️  Available tools:")
                for tool in tools:
                    print(f"  - {tool}")
                continue
            
            # Process user input
            print("🤖 Agent: ", end="", flush=True)
            response = await agent.chat(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again or type 'quit' to exit")
    
    # Cleanup
    try:
        await agent.cleanup()
    except:
        pass

if __name__ == "__main__":
    asyncio.run(main())