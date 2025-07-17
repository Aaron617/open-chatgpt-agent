"""
Terminal tool for executing system commands
"""
import asyncio
import os
from typing import Optional
from .base_tool import BaseTool, ToolResult
from ..utils.config import config

class TerminalTool(BaseTool):
    """Tool for executing terminal commands"""
    
    def __init__(self):
        super().__init__(
            name="terminal",
            description="Execute terminal/shell commands and return output"
        )
        self.timeout = config.TERMINAL_TIMEOUT / 1000  # Convert to seconds
        self.shell = config.TERMINAL_SHELL
        self.working_dir = config.TERMINAL_WORKING_DIR
    
    async def execute(self, command: str, working_directory: Optional[str] = None) -> ToolResult:
        """Execute a terminal command"""
        try:
            # Determine working directory
            work_dir = working_directory or self.working_dir
            if work_dir and not os.path.exists(work_dir):
                os.makedirs(work_dir, exist_ok=True)
            
            # Prepare command based on shell
            if self.shell == "bash":
                cmd = ["bash", "-c", command]
            elif self.shell == "zsh":
                cmd = ["zsh", "-c", command]
            elif self.shell == "sh":
                cmd = ["sh", "-c", command]
            else:
                cmd = [self.shell, "-c", command]
            
            # Execute command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir if work_dir and os.path.exists(work_dir) else None
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
                
                stdout_str = stdout.decode('utf-8') if stdout else ""
                stderr_str = stderr.decode('utf-8') if stderr else ""
                
                # Format output
                output = ""
                if stdout_str:
                    output += f"STDOUT:\n{stdout_str}"
                if stderr_str:
                    if output:
                        output += "\n\n"
                    output += f"STDERR:\n{stderr_str}"
                
                if not output:
                    output = "Command executed successfully (no output)"
                
                success = process.returncode == 0
                error = stderr_str if not success else None
                
                return ToolResult(
                    success=success,
                    content=output,
                    error=error,
                    metadata={
                        "command": command,
                        "return_code": process.returncode,
                        "working_directory": work_dir,
                        "shell": self.shell
                    }
                )
                
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Command timed out after {self.timeout} seconds"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Terminal command failed: {str(e)}"
            )
    
    async def change_directory(self, path: str) -> ToolResult:
        """Change the working directory"""
        try:
            if not os.path.exists(path):
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Directory does not exist: {path}"
                )
            
            if not os.path.isdir(path):
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Path is not a directory: {path}"
                )
            
            # Update working directory
            self.working_dir = os.path.abspath(path)
            
            return ToolResult(
                success=True,
                content=f"Changed directory to: {self.working_dir}",
                metadata={"new_directory": self.working_dir}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Failed to change directory: {str(e)}"
            )
    
    async def get_current_directory(self) -> ToolResult:
        """Get the current working directory"""
        try:
            return ToolResult(
                success=True,
                content=f"Current directory: {self.working_dir}",
                metadata={"current_directory": self.working_dir}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Failed to get current directory: {str(e)}"
            )