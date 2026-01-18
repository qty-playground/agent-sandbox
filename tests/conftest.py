"""
Shared pytest fixtures for agent-sandbox tests.
"""
import os
import subprocess
from pathlib import Path
from typing import Generator

import pytest

from tests.agent_commands import create_agent_command, AgentCommand


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--agent",
        action="store",
        default="claude",
        help="Agent to test: claude, codex, or gemini (default: claude)",
    )
    parser.addoption(
        "--skip-ssh-check",
        action="store_true",
        default=False,
        help="Skip SSH agent availability check",
    )


def pytest_configure(config):
    """Configure pytest session."""
    agent = config.getoption("--agent")
    print(f"\n=== Testing with agent: {agent} ===")


@pytest.fixture(scope="session")
def agent_type(request) -> str:
    """Get the agent type from command line option."""
    return request.config.getoption("--agent")


@pytest.fixture(scope="session")
def check_ssh_agent(request) -> bool:
    """
    Check if SSH agent is available and has keys loaded.

    This is required for git operations in tests.
    """
    if request.config.getoption("--skip-ssh-check"):
        return True

    # Check if SSH_AUTH_SOCK is set
    if not os.environ.get("SSH_AUTH_SOCK"):
        pytest.skip("SSH_AUTH_SOCK not set. SSH agent is not running.")

    # Check if ssh-add -l succeeds
    try:
        result = subprocess.run(
            ["ssh-add", "-l"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            pytest.skip(
                "SSH agent has no identities. Please run: ssh-add ~/.ssh/your_key"
            )
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip("Failed to check SSH agent status")


@pytest.fixture(scope="session")
def check_agbox_installed():
    """Check if agbox is installed and accessible."""
    try:
        result = subprocess.run(
            ["agbox", "--help"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode != 0:
            pytest.skip("agbox is not installed or not accessible in PATH")
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip("agbox is not installed or not accessible in PATH")


@pytest.fixture(scope="session")
def check_agent_installed(agent_type: str, check_agbox_installed):
    """
    Check if the specified agent is installed and accessible via agbox.

    Instead of checking if the agent command exists directly (which fails for aliases),
    we test if agbox can execute the agent with a simple command.
    """
    try:
        # Try to execute a simple command with agbox + agent
        # This verifies both agbox and the agent are working
        result = subprocess.run(
            ["agbox", "--dry-run", agent_type],
            capture_output=True,
            timeout=5,
        )
        # --dry-run should succeed if agent is recognized by agbox
        if result.returncode != 0:
            pytest.skip(
                f"Agent '{agent_type}' is not accessible via agbox. "
                f"Make sure the agent is installed and agbox can find it."
            )
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip(f"Failed to check if agent '{agent_type}' is accessible via agbox")


@pytest.fixture
def work_dir(request) -> Generator[Path, None, None]:
    """
    Create a temporary working directory for tests in project root.

    Unlike using /tmp (which has unrestricted write access in sandbox),
    this creates test directories under project root to properly test
    sandbox restrictions. The working directory will have write access
    via agbox's --work-dir, while other locations remain protected.

    Each test gets its own isolated directory that is cleaned up after the test.
    """
    import time
    import shutil

    # Get project root (parent of tests directory)
    project_root = Path(__file__).parent.parent

    # Create unique test directory name
    test_name = request.node.name
    timestamp = int(time.time() * 1000000)  # microseconds for uniqueness
    test_dir = project_root / f".pytest-tmp-{test_name}-{timestamp}"

    # Create directory
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        yield test_dir
    finally:
        # Cleanup after test
        if test_dir.exists():
            shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def agent_cmd(agent_type: str, work_dir: Path, check_agbox_installed, check_agent_installed) -> AgentCommand:
    """
    Create an agent command instance for the current test.

    This fixture depends on:
    - agent_type: from command line option
    - work_dir: temporary directory for the test
    - check_agbox_installed: ensures agbox is available
    - check_agent_installed: ensures the agent is available
    """
    return create_agent_command(agent_type, work_dir=work_dir, timeout=60)


@pytest.fixture
def git_repo(work_dir: Path, check_ssh_agent) -> Generator[Path, None, None]:
    """
    Create a temporary git repository for testing.

    This fixture:
    1. Initializes a git repo in the work_dir
    2. Configures git user for commits
    3. Creates an initial commit
    4. Yields the repo path
    5. Cleans up on teardown
    """
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=work_dir, check=True, capture_output=True)

    # Configure git user
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=work_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=work_dir,
        check=True,
        capture_output=True,
    )

    # Create initial commit
    readme = work_dir / "README.md"
    readme.write_text("# Test Repository\n\nThis is a test repository.\n")

    subprocess.run(["git", "add", "README.md"], cwd=work_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=work_dir,
        check=True,
        capture_output=True,
    )

    yield work_dir

    # Cleanup is automatic with tmp_path


@pytest.fixture
def sample_file(work_dir: Path) -> Path:
    """Create a sample file for testing file operations."""
    file_path = work_dir / "sample.txt"
    file_path.write_text("Hello, World!\n")
    return file_path
