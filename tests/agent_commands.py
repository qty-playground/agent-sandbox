"""
Agent command abstraction for testing different agents.

This module provides a common interface for executing agent commands
with different agents (claude, codex, gemini) through agbox.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import subprocess


@dataclass
class CommandResult:
    """Result of executing an agent command."""
    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        """Whether the command succeeded."""
        return self.returncode == 0

    @property
    def has_permission_error(self) -> bool:
        """Whether the command encountered permission errors."""
        return "Operation not permitted" in self.stderr or "Operation not permitted" in self.stdout


class AgentCommand(ABC):
    """Abstract base class for agent commands."""

    def __init__(self, work_dir: Optional[Path] = None, timeout: int = 60):
        """
        Initialize agent command.

        Args:
            work_dir: Working directory for the agent (default: current directory)
            timeout: Timeout in seconds for command execution
        """
        self.work_dir = work_dir or Path.cwd()
        self.timeout = timeout

    @abstractmethod
    def get_command_args(self, prompt: str) -> List[str]:
        """
        Get the command line arguments for the agent.

        Args:
            prompt: The prompt to send to the agent

        Returns:
            List of command line arguments
        """
        pass

    def execute(self, prompt: str, check: bool = True) -> CommandResult:
        """
        Execute the agent command with the given prompt.

        Args:
            prompt: The prompt to send to the agent
            check: Whether to check for non-zero return code

        Returns:
            CommandResult with execution results
        """
        cmd = self.get_command_args(prompt)

        try:
            result = subprocess.run(
                cmd,
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            if check and result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode,
                    cmd,
                    result.stdout,
                    result.stderr,
                )

            return CommandResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except subprocess.TimeoutExpired as e:
            return CommandResult(
                returncode=-1,
                stdout=e.stdout or "",
                stderr=f"Command timed out after {self.timeout} seconds",
            )


class ClaudeCommand(AgentCommand):
    """Claude agent command implementation."""

    def get_command_args(self, prompt: str) -> List[str]:
        """
        Get command args for Claude.

        Claude uses the -p flag for non-interactive prompt execution.
        Uses haiku model for faster and cheaper testing.
        Bypasses permissions for automated testing in sandbox environment.
        Forces English output for consistent test assertions.
        """
        return [
            "agbox",
            "claude",
            "--model", "haiku",
            "--permission-mode", "bypassPermissions",
            "--append-system-prompt", "Always respond in English",
            "-p", prompt
        ]


class CodexCommand(AgentCommand):
    """Codex agent command implementation."""

    def get_command_args(self, prompt: str) -> List[str]:
        """
        Get command args for Codex.

        Codex uses the exec subcommand for non-interactive execution.
        """
        return ["agbox", "codex", "exec", prompt]


class GeminiCommand(AgentCommand):
    """Gemini agent command implementation."""

    def get_command_args(self, prompt: str) -> List[str]:
        """
        Get command args for Gemini.

        Gemini uses -y flag (yolo mode) with positional prompt.
        """
        return ["agbox", "gemini", "-y", prompt]


def create_agent_command(agent_type: str, work_dir: Optional[Path] = None, timeout: int = 60) -> AgentCommand:
    """
    Factory function to create agent command instances.

    Args:
        agent_type: Type of agent ("claude", "codex", or "gemini")
        work_dir: Working directory for the agent
        timeout: Timeout in seconds

    Returns:
        AgentCommand instance for the specified agent type

    Raises:
        ValueError: If agent_type is not supported
    """
    agents = {
        "claude": ClaudeCommand,
        "codex": CodexCommand,
        "gemini": GeminiCommand,
    }

    agent_class = agents.get(agent_type.lower())
    if not agent_class:
        raise ValueError(f"Unsupported agent type: {agent_type}. Supported types: {list(agents.keys())}")

    return agent_class(work_dir=work_dir, timeout=timeout)
