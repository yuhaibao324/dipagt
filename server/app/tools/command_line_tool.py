import asyncio
import os
import json
import shlex
from typing import Any, Dict, Optional, AsyncIterator
import logging

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class CommandLineTool(BaseTool):
    """
    执行命令行操作的工具
    """
    
    def __init__(self):
        super().__init__(
            name="CommandLineTool",
            description="执行命令行操作"
        )
        self.allowed_commands = []
        self.blocked_commands = ["rm -rf", "sudo", "format", "mkfs"]
    
    def configure(self, allowed_commands: Optional[list] = None, blocked_commands: Optional[list] = None):
        """
        配置命令行工具
        
        Args:
            allowed_commands: 允许执行的命令列表，为空则允许所有未被阻止的命令
            blocked_commands: 禁止执行的命令列表
        """
        if allowed_commands is not None:
            self.allowed_commands = allowed_commands
        
        if blocked_commands is not None:
            self.blocked_commands = blocked_commands
    
    def _is_command_allowed(self, command: str) -> bool:
        """
        检查命令是否被允许执行
        
        Args:
            command: 要检查的命令
            
        Returns:
            命令是否被允许
        """
        # 检查是否包含被阻止的命令
        for blocked in self.blocked_commands:
            if blocked in command:
                return False
        
        # 如果没有设置允许列表，则允许所有未被阻止的命令
        if not self.allowed_commands:
            return True
        
        # 检查是否在允许列表中
        for allowed in self.allowed_commands:
            if command.startswith(allowed):
                return True
        
        return False
    
    async def _run(self,
                   command: str,
                   working_directory: Optional[str] = None,
                   timeout: int = 60,
                   env_vars: Optional[Dict[str, str]] = None,
                   **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """
        执行命令行操作并流式返回输出
        
        Args:
            command: 要执行的命令
            working_directory: 工作目录
            timeout: 超时时间（秒）
            env_vars: 环境变量
            **kwargs: 可选参数，包含 conversation_context
            
        Yields:
            字典，包含命令输出（stdout/stderr）、状态信息或错误.
            Example chunk: {"type": "stdout_chunk", "data": "..."}
            Example chunk: {"type": "stderr_chunk", "data": "..."}
            Example status: {"type": "status", "message": "Executing..."}
            Example final: {"type": "final_status", "status": "success", "return_code": 0, "command": cmd}
            Example error: {"type": "error", "error": "...", "command": cmd}
        """
        if not self._is_command_allowed(command):
            yield {"type": "error", "error": "Command execution is not allowed on this system."}
            return
        
        conversation_context = kwargs.get("conversation_context")
        # Note: conversation_context is retrieved but not currently used in command execution.

        # 设置工作目录
        cwd = working_directory or os.getcwd()
        
        # 设置环境变量
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
        
        process = None
        try:
            yield {"type": "status", "message": f"Executing command in {cwd}: {command}"}
            logger.info(f"Executing command in {cwd}: {command}")
            
            # 使用asyncio.create_subprocess_shell执行命令
            # Note: Using shell=True has security implications if the command is constructed from untrusted input.
            # Consider using create_subprocess_exec if the command and args can be safely split.
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env
            )
            
            yield {"type": "status", "message": f"Process started (PID: {process.pid})"}

            # Asynchronously read stdout and stderr
            async def read_stream(stream, stream_type):
                while True:
                    try:
                        # Read up to 1kb at a time, adjust buffer size if needed
                        chunk = await stream.read(1024)
                        if not chunk:
                            break
                        yield {"type": "content_chunk", "content": chunk.decode("utf-8", errors="replace")}
                    except Exception as e:
                        logger.error(f"Error reading {stream_type}: {e}")
                        yield {"type": "error", "error": f"Error reading {stream_type}: {e}"}
                        break # Stop reading this stream on error

            stdout_task = asyncio.create_task(read_stream(process.stdout, "stdout"))
            stderr_task = asyncio.create_task(read_stream(process.stderr, "stderr"))

            # Wait for the process to complete or timeout
            try:
                # Wait for streams to finish AND process to exit
                _, _, return_code = await asyncio.wait_for(
                    asyncio.gather(stdout_task, stderr_task, process.wait()), 
                    timeout=timeout
                )
                status = "success" if return_code == 0 else "error"
                yield {"type": "final_status", "status": status, "return_code": return_code, "command": command}

            except asyncio.TimeoutError:
                logger.warning(f"Command '{command}' timed out after {timeout} seconds.")
                yield {"type": "error", "command": command, "error": f"Command execution timed out after {timeout} seconds"}
                # Attempt to kill the process
                try:
                    process.kill()
                    logger.info(f"Killed timed-out process {process.pid}")
                    yield {"type": "status", "message": "Process killed due to timeout."}
                except ProcessLookupError:
                    logger.warning(f"Process {process.pid} already exited before kill attempt.")
                except Exception as kill_e:
                    logger.error(f"Error killing process {process.pid}: {kill_e}")
                # Ensure stream tasks are cancelled if they are still running
                if not stdout_task.done(): stdout_task.cancel()
                if not stderr_task.done(): stderr_task.cancel()
                await asyncio.gather(stdout_task, stderr_task, return_exceptions=True) # Wait for cancellation
            
        except FileNotFoundError:
             logger.error(f"Command not found: {shlex.split(command)[0]}")
             yield {"type": "error", "command": command, "error": f"Command not found: {shlex.split(command)[0]}"}
        except Exception as e:
            logger.error(f"Error executing command '{command}': {str(e)}")
            yield {"type": "error", "command": command, "error": f"Failed to execute command: {str(e)}"}
        finally:
             # Ensure process is terminated if it exists and is still running unexpectedly
             if process and process.returncode is None:
                 logger.warning(f"Process {process.pid} might still be running after exit/error. Attempting kill.")
                 try:
                     process.kill()
                 except Exception as final_kill_e:
                     logger.error(f"Error during final kill attempt for process {process.pid}: {final_kill_e}")

    
    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的JSON Schema
        """
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的命令"
                },
                "working_directory": {
                    "type": "string",
                    "description": "工作目录"
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（秒）",
                    "default": 60
                },
                "env_vars": {
                    "type": "object",
                    "description": "环境变量"
                }
            },
            "required": ["command"]
        } 