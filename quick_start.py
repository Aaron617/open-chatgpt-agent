#!/usr/bin/env python3
"""
Quick start script for the Open ChatGPT Agent
This script provides a simple way to test the agent with minimal setup
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def quick_demo():
    """Quick demo of the agent"""
    print("🚀 Open ChatGPT Agent - Quick Demo")
    print("=" * 50)
    
    # Check if we have any API keys
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if not (anthropic_key or openai_key or gemini_key):
        print("❌ No API keys found!")
        print("Please set at least one of these environment variables:")
        print("  - ANTHROPIC_API_KEY")
        print("  - OPENAI_API_KEY") 
        print("  - GEMINI_API_KEY")
        print("\nOr create a .env file with your API keys.")
        return
    
    # Determine which provider to use
    provider = "anthropic" if anthropic_key else "openai" if openai_key else "gemini"
    print(f"✅ Using {provider} as the AI provider")
    
    try:
        from agent import ChatGPTAgent
        
        # Create agent
        agent = ChatGPTAgent(
            model_provider=provider,
            enable_mcp=False,  # Disable MCP for quick demo
            enable_logging=False
        )
        
        print("🤖 Agent initialized successfully!")
        print("\n💬 Try asking something like:")
        print("  - 'Hello, how are you?'")
        print("  - 'What can you help me with?'")
        print("  - 'Execute this Python code: print(2+2)'")
        print("\nType 'quit' to exit")
        print("-" * 50)
        
        # Simple chat loop
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() == 'quit':
                    print("👋 Goodbye!")
                    break
                
                print("🤖 Agent: ", end="", flush=True)
                response = await agent.chat(user_input)
                print(response)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # Cleanup
        await agent.cleanup()
        
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        print("Please check your API keys and try again")

if __name__ == "__main__":
    asyncio.run(quick_demo())