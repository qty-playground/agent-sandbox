"""
Baseline tests for agent operations in agbox sandbox.

These tests verify that agents can perform core operations:
- Agent launch and working directory access
- File operations (read, write, edit)
- Git operations (branch, commit, push, pull, delete)
- Script execution

Test cases correspond to the test plan in docs/test-plan.md
"""
import subprocess
from pathlib import Path

import pytest

from tests.agent_commands import AgentCommand


class TestAgentBasicOperations:
    """TC-1: Agent Basic Launch and Working Directory Access"""

    def test_agent_can_access_working_directory(self, agent_cmd: AgentCommand):
        """
        Verify that the agent can launch and access the working directory
        without permission errors.
        """
        result = agent_cmd.execute(
            "what is the current working directory path?",
            check=False,
        )

        # Should not have permission errors
        assert not result.has_permission_error, (
            f"Permission error detected:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # Should succeed
        assert result.success, (
            f"Agent failed to execute:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # Should return working directory path
        work_dir_str = str(agent_cmd.work_dir)
        assert work_dir_str in result.stdout, (
            f"Working directory '{work_dir_str}' not found in output:\n{result.stdout}"
        )


class TestFileOperations:
    """TC-2, TC-3, TC-4: File Read, Write, and Edit Operations"""

    def test_agent_can_read_files(self, agent_cmd: AgentCommand, sample_file: Path):
        """TC-2: Verify agent can read files in the working directory."""
        result = agent_cmd.execute(
            f"read the {sample_file.name} file and tell me what it contains",
            check=False,
        )

        assert not result.has_permission_error, (
            f"Permission error detected:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        assert result.success, (
            f"Agent failed to read file:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # Should mention the content
        assert "Hello" in result.stdout or "World" in result.stdout, (
            f"File content not found in output:\n{result.stdout}"
        )

    def test_agent_can_write_files(self, agent_cmd: AgentCommand, work_dir: Path):
        """TC-3: Verify agent can create and write files in the working directory."""
        test_file = "test-hello.txt"
        test_content = "Hello from agbox test"

        result = agent_cmd.execute(
            f"create a new file called {test_file} with content '{test_content}'",
            check=False,
        )

        assert not result.has_permission_error, (
            f"Permission error detected:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        assert result.success, (
            f"Agent failed to write file:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # Verify file was created
        file_path = work_dir / test_file
        assert file_path.exists(), f"File {test_file} was not created"

        # Verify content
        content = file_path.read_text()
        assert test_content in content, (
            f"Expected content '{test_content}' not found in file. Got: {content}"
        )

    def test_agent_can_edit_files(self, agent_cmd: AgentCommand, work_dir: Path):
        """TC-4: Verify agent can edit existing files in the working directory."""
        # First create a file
        test_file = work_dir / "test-hello.txt"
        test_file.write_text("Hello from agbox test\n")

        # Now ask agent to edit it
        result = agent_cmd.execute(
            f"edit {test_file.name} and append a new line 'Modified by agent'",
            check=False,
        )

        assert not result.has_permission_error, (
            f"Permission error detected:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        assert result.success, (
            f"Agent failed to edit file:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # Verify file was modified
        content = test_file.read_text()
        assert "Hello from agbox test" in content, "Original content was lost"
        assert "Modified by agent" in content, "New content was not added"


class TestScriptExecution:
    """TC-8: Script Execution"""

    def test_agent_can_execute_scripts(self, agent_cmd: AgentCommand, work_dir: Path):
        """Verify agent can execute scripts in the working directory."""
        # Create a test script with unique output marker
        script_path = work_dir / "test-script.sh"
        unique_marker = "TEST_MARKER_12345"
        script_content = f"""#!/bin/bash
echo "{unique_marker}"
echo "Current directory: $(pwd)"
"""
        script_path.write_text(script_content)
        script_path.chmod(0o755)

        result = agent_cmd.execute(
            "Execute the test-script.sh script using bash and show me its complete output",
            check=False,
        )

        assert not result.has_permission_error, (
            f"Permission error detected:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        assert result.success, (
            f"Agent failed to execute script:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # Verify script was actually executed by checking for unique marker
        assert unique_marker in result.stdout, (
            f"Script output marker '{unique_marker}' not found. "
            f"Script may not have been executed.\nOutput:\n{result.stdout}"
        )


class TestGitOperations:
    """TC-5, TC-6, TC-7: Git Operations (branch, commit, push, pull, delete)"""

    def test_agent_can_create_and_commit(self, agent_cmd: AgentCommand, git_repo: Path):
        """TC-5 (part 1): Verify agent can create branches and commit changes."""
        # Create a test file first
        test_file = git_repo / "test-file.txt"
        test_file.write_text("Test content\n")

        result = agent_cmd.execute(
            "create a new git branch called test-agent-branch, "
            "add the test-file.txt file, and commit with message 'test commit from agent'",
            check=False,
        )

        assert not result.has_permission_error, (
            f"Permission error detected:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        assert result.success, (
            f"Agent failed git operations:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # Verify branch was created
        branches_result = subprocess.run(
            ["git", "branch", "--list", "test-agent-branch"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert "test-agent-branch" in branches_result.stdout, (
            "Branch test-agent-branch was not created"
        )

        # Verify file was committed
        log_result = subprocess.run(
            ["git", "log", "--oneline", "test-agent-branch"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert "test commit from agent" in log_result.stdout, (
            "Commit message not found in git log"
        )

    def test_agent_can_switch_branches(self, agent_cmd: AgentCommand, git_repo: Path):
        """TC-6: Verify agent can switch branches and pull changes."""
        # Create a test branch first
        subprocess.run(
            ["git", "checkout", "-b", "test-branch"],
            cwd=git_repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=git_repo,
            check=True,
            capture_output=True,
        )

        result = agent_cmd.execute(
            "switch to test-branch branch",
            check=False,
        )

        assert not result.has_permission_error, (
            f"Permission error detected:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        assert result.success, (
            f"Agent failed to switch branches:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # Verify current branch
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert "test-branch" in branch_result.stdout, (
            f"Not on test-branch. Current branch: {branch_result.stdout}"
        )

    def test_agent_can_delete_branches(self, agent_cmd: AgentCommand, git_repo: Path):
        """TC-7: Verify agent can delete local branches."""
        # Create a test branch first
        subprocess.run(
            ["git", "checkout", "-b", "test-delete-branch"],
            cwd=git_repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=git_repo,
            check=True,
            capture_output=True,
        )

        result = agent_cmd.execute(
            "delete the test-delete-branch branch locally",
            check=False,
        )

        assert not result.has_permission_error, (
            f"Permission error detected:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        assert result.success, (
            f"Agent failed to delete branch:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # Verify branch was deleted
        branches_result = subprocess.run(
            ["git", "branch", "--list", "test-delete-branch"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert "test-delete-branch" not in branches_result.stdout, (
            "Branch test-delete-branch was not deleted"
        )
