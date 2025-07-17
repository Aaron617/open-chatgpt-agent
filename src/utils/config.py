"""
Simplified configuration management using only environment variables
"""
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Simple configuration class using environment variables"""
    
    # AI Model API Keys
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Search API Keys
    EXA_API_KEY: str = os.getenv("EXA_API_KEY", "")
    GOOGLE_SEARCH_API_KEY: str = os.getenv("GOOGLE_SEARCH_API_KEY", "")
    GOOGLE_SEARCH_ENGINE_ID: str = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")
    
    # Model Configuration
    DEFAULT_MODEL_PROVIDER: str = os.getenv("DEFAULT_MODEL_PROVIDER", "anthropic")
    DEFAULT_MODEL_NAME: str = os.getenv("DEFAULT_MODEL_NAME", "claude-sonnet-4-20250514")
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    DEFAULT_MAX_TOKENS: Optional[int] = int(os.getenv("DEFAULT_MAX_TOKENS", "4096")) if os.getenv("DEFAULT_MAX_TOKENS") else None
    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "60"))
    
    # Agent Configuration
    SESSION_LOG_DIR: str = os.getenv("SESSION_LOG_DIR", "./logs")
    ENABLE_LOGGING: bool = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Browser Configuration
    BROWSER_HEADLESS: bool = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
    BROWSER_TIMEOUT: int = int(os.getenv("BROWSER_TIMEOUT", "30000"))
    BROWSER_USER_AGENT: str = os.getenv("BROWSER_USER_AGENT", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
    # Code Execution Configuration
    CODE_EXECUTION_TIMEOUT: int = int(os.getenv("CODE_EXECUTION_TIMEOUT", "60"))
    ALLOWED_CODE_TYPES: list = os.getenv("ALLOWED_CODE_TYPES", "python,bash,r").split(",")
    ENABLE_CODE_EXECUTION: bool = os.getenv("ENABLE_CODE_EXECUTION", "true").lower() == "true"
    
    # Terminal Configuration
    TERMINAL_SHELL: str = os.getenv("TERMINAL_SHELL", "bash")
    TERMINAL_TIMEOUT: int = int(os.getenv("TERMINAL_TIMEOUT", "10000"))
    TERMINAL_WORKING_DIR: str = os.getenv("TERMINAL_WORKING_DIR", "./workspace")
    
    # MCP Configuration
    ENABLE_MCP: bool = os.getenv("ENABLE_MCP", "false").lower() == "true"
    MCP_BROWSER_SERVER: str = os.getenv("MCP_BROWSER_SERVER", "browser_use")
    MCP_BROWSER_COMMAND: str = os.getenv("MCP_BROWSER_COMMAND", "npx")
    MCP_BROWSER_ARGS: str = os.getenv("MCP_BROWSER_ARGS", "@co-browser/browser-use-mcp")
    
    @classmethod
    def get_api_key(cls, provider: str) -> str:
        """Get API key for a specific provider"""
        key_map = {
            "anthropic": cls.ANTHROPIC_API_KEY,
            "openai": cls.OPENAI_API_KEY,
            "gemini": cls.GEMINI_API_KEY,
            "exa": cls.EXA_API_KEY,
            "google_search": cls.GOOGLE_SEARCH_API_KEY
        }
        return key_map.get(provider, "")
    
    @classmethod
    def get_model_config(cls, provider: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get model configuration for a specific provider"""
        return {
            "model_name": model_name or cls.DEFAULT_MODEL_NAME,
            "api_key": cls.get_api_key(provider),
            "temperature": cls.DEFAULT_TEMPERATURE,
            "max_tokens": cls.DEFAULT_MAX_TOKENS,
            "timeout": cls.DEFAULT_TIMEOUT
        }
    
    @classmethod
    def validate_config(cls) -> Dict[str, bool]:
        """Validate configuration and return status"""
        validation = {
            "anthropic": bool(cls.ANTHROPIC_API_KEY),
            "openai": bool(cls.OPENAI_API_KEY),
            "gemini": bool(cls.GEMINI_API_KEY),
            "exa": bool(cls.EXA_API_KEY),
            "google_search": bool(cls.GOOGLE_SEARCH_API_KEY and cls.GOOGLE_SEARCH_ENGINE_ID)
        }
        return validation
    
    @classmethod
    def get_missing_keys(cls) -> list:
        """Get list of missing API keys"""
        validation = cls.validate_config()
        return [key for key, valid in validation.items() if not valid]
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available AI providers"""
        providers = []
        if cls.ANTHROPIC_API_KEY:
            providers.append("anthropic")
        if cls.OPENAI_API_KEY:
            providers.append("openai")
        if cls.GEMINI_API_KEY:
            providers.append("gemini")
        return providers
    
    @classmethod
    def get_preferred_provider(cls) -> str:
        """Get preferred provider, falling back to available ones"""
        available = cls.get_available_providers()
        
        if cls.DEFAULT_MODEL_PROVIDER in available:
            return cls.DEFAULT_MODEL_PROVIDER
        
        # Fallback to first available provider
        if available:
            return available[0]
        
        # No valid providers available
        raise ValueError("No valid API keys found for any provider")
    
    @classmethod
    def print_config_status(cls):
        """Print configuration status"""
        print("Configuration Status:")
        print("=" * 50)
        
        # Show preferred provider
        try:
            preferred = cls.get_preferred_provider()
            print(f"Preferred provider: {preferred}")
        except ValueError as e:
            print(f"Error: {e}")
        
        print("\nAPI Key Status:")
        validation = cls.validate_config()
        for service, valid in validation.items():
            status = "✓" if valid else "✗"
            print(f"{service:<15}: {status}")
        
        # Show available providers
        available = cls.get_available_providers()
        if available:
            print(f"\nAvailable providers: {', '.join(available)}")
        else:
            print("\nNo API keys configured!")
            print("Please set API keys in your .env file")
        
        # Show tool status
        print(f"\nTool Status:")
        print(f"code_execution   : {'✓' if cls.ENABLE_CODE_EXECUTION else '✗'}")
        print(f"web_search       : {'✓' if cls.EXA_API_KEY else '✗'}")
        print(f"mcp_browser      : {'✓' if cls.ENABLE_MCP else '✗'}")
        print(f"logging          : {'✓' if cls.ENABLE_LOGGING else '✗'}")

# Global config instance
config = Config()