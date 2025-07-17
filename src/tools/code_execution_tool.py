"""
Code execution tool for running Python, Bash, and R code
"""
import asyncio
import subprocess
import tempfile
import os
from typing import Optional
from .base_tool import BaseTool, ToolResult
from ..utils.config import config

class CodeExecutionTool(BaseTool):
    """Tool for executing code in various languages"""
    
    def __init__(self):
        super().__init__(
            name="code_execution",
            description="Execute Python, Bash, or R code and return the output"
        )
        self.timeout = config.CODE_EXECUTION_TIMEOUT
        self.allowed_types = config.ALLOWED_CODE_TYPES
    
    async def execute(self, code: str, code_type: str = "python") -> ToolResult:
        """Execute code and return result"""
        try:
            if not config.ENABLE_CODE_EXECUTION:
                return ToolResult(
                    success=False,
                    content="",
                    error="Code execution is disabled"
                )
            
            if code_type not in self.allowed_types:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Code type '{code_type}' not allowed. Allowed types: {', '.join(self.allowed_types)}"
                )
            
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(mode='w', suffix=self._get_file_extension(code_type), delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Get command for code type
                command = self._get_command(code_type, temp_file)
                
                # Execute code
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=config.TERMINAL_WORKING_DIR if os.path.exists(config.TERMINAL_WORKING_DIR) else None
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=self.timeout
                    )
                    
                    stdout_str = stdout.decode('utf-8') if stdout else ""
                    stderr_str = stderr.decode('utf-8') if stderr else ""
                    
                    # Combine stdout and stderr
                    output = stdout_str
                    if stderr_str:
                        output += f"\nSTDERR:\n{stderr_str}"
                    
                    success = process.returncode == 0
                    error = stderr_str if not success else None
                    
                    return ToolResult(
                        success=success,
                        content=output,
                        error=error,
                        metadata={
                            "code_type": code_type,
                            "return_code": process.returncode,
                            "execution_time": self.timeout
                        }
                    )
                    
                except asyncio.TimeoutError:
                    process.kill()
                    return ToolResult(
                        success=False,
                        content="",
                        error=f"Code execution timed out after {self.timeout} seconds"
                    )
                    
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Code execution failed: {str(e)}"
            )
    
    def _get_file_extension(self, code_type: str) -> str:
        """Get file extension for code type"""
        extensions = {
            "python": ".py",
            "bash": ".sh",
            "r": ".r"
        }
        return extensions.get(code_type, ".txt")
    
    def _get_command(self, code_type: str, file_path: str) -> list:
        """Get command to execute code"""
        commands = {
            "python": ["python", file_path],
            "bash": ["bash", file_path],
            "r": ["Rscript", file_path]
        }
        return commands.get(code_type, ["cat", file_path])