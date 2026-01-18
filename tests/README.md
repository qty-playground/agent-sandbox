# Agent Sandbox Tests

Pytest-based tests for agbox agent functionality, replacing the original manual prompt-based testing approach.

## Test Architecture

### Test Modules

- `agent_commands.py`: Agent command abstraction layer providing unified interface for different agents
  - `AgentCommand`: Abstract base class
  - `ClaudeCommand`: Claude agent implementation
  - `CodexCommand`: Codex agent implementation (extensible)
  - `GeminiCommand`: Gemini agent implementation (extensible)

- `conftest.py`: pytest fixtures and configuration
  - `agent_type`: Get agent type from command line
  - `agent_cmd`: Create agent command instance
  - `work_dir`: Temporary working directory
  - `git_repo`: Temporary git repository
  - `check_ssh_agent`: Check SSH agent status

- `test_agent_baseline.py`: Baseline test cases
  - TC-1: Agent launch and working directory access
  - TC-2: File read operations
  - TC-3: File write operations
  - TC-4: File edit operations
  - TC-5: Git branch creation and commits
  - TC-6: Git branch switching
  - TC-7: Git branch deletion
  - TC-8: Script execution

## Environment Setup

### Install Test Dependencies

```bash
# Using venv
source venv/bin/activate
pip install -e ".[test]"

# Or install pytest directly
pip install pytest pytest-timeout
```

### Prerequisites

1. agbox must be installed and accessible in PATH
2. The agent to test (claude/codex/gemini) must be installed
3. For git operation tests, SSH agent must be configured:
   ```bash
   ssh-add ~/.ssh/your_key
   ```

## Running Tests

### Basic Usage

```bash
# Run all tests (default: claude agent)
pytest tests/

# Specify agent to test
pytest tests/ --agent=claude
pytest tests/ --agent=codex
pytest tests/ --agent=gemini

# Run specific test class
pytest tests/test_agent_baseline.py::TestAgentBasicOperations

# Run specific test case
pytest tests/test_agent_baseline.py::TestFileOperations::test_agent_can_write_files
```

### Advanced Options

```bash
# Show verbose output
pytest tests/ -v

# Show print output
pytest tests/ -s

# Skip SSH agent check
pytest tests/ --skip-ssh-check

# Parallel execution (requires pytest-xdist)
pip install pytest-xdist
pytest tests/ -n auto
```

## Test Output Example

```
$ pytest tests/ --agent=claude -v

=== Testing with agent: claude ===

tests/test_agent_baseline.py::TestAgentBasicOperations::test_agent_can_access_working_directory PASSED
tests/test_agent_baseline.py::TestFileOperations::test_agent_can_read_files PASSED
tests/test_agent_baseline.py::TestFileOperations::test_agent_can_write_files PASSED
tests/test_agent_baseline.py::TestFileOperations::test_agent_can_edit_files PASSED
tests/test_agent_baseline.py::TestScriptExecution::test_agent_can_execute_scripts PASSED
tests/test_agent_baseline.py::TestGitOperations::test_agent_can_create_and_commit PASSED
tests/test_agent_baseline.py::TestGitOperations::test_agent_can_switch_branches PASSED
tests/test_agent_baseline.py::TestGitOperations::test_agent_can_delete_branches PASSED

=== 8 passed in 45.23s ===
```

## Extending Tests

### Adding New Agent Support

1. Add agent class in `agent_commands.py`:
   ```python
   class NewAgentCommand(AgentCommand):
       def get_command_args(self, prompt: str) -> List[str]:
           return ["agbox", "new-agent", "exec", prompt]
   ```

2. Register in `create_agent_command` factory:
   ```python
   agents = {
       "claude": ClaudeCommand,
       "codex": CodexCommand,
       "gemini": GeminiCommand,
       "new-agent": NewAgentCommand,  # Add new agent
   }
   ```

3. Run tests:
   ```bash
   pytest tests/ --agent=new-agent
   ```

### Adding Test Cases

Add test methods in `test_agent_baseline.py`:

```python
class TestNewFeature:
    """Test description"""

    def test_new_feature(self, agent_cmd: AgentCommand, work_dir: Path):
        """Test new functionality"""
        result = agent_cmd.execute("your prompt here", check=False)

        assert not result.has_permission_error
        assert result.success
        # Additional assertions...
```

## Known Limitations

1. Remote git operation tests (push, pull from remote) require actual remote repository, currently marked as skip
2. Tests depend on actual agent execution results, may need adjustment if agent behavior changes
3. Some tests may be slow (waiting for agent execution to complete)

## Troubleshooting

### SSH Agent Related Errors

If you see "SSH agent has no identities" error:

```bash
# Verify SSH agent is running
echo $SSH_AUTH_SOCK

# Load SSH key
ssh-add ~/.ssh/your_key

# Verify key is loaded
ssh-add -l
```

### agbox Not Found

```bash
# Verify agbox is installed
which agbox

# If not, install it
pip install -e .
```

### Agent Not Found

```bash
# Verify agent is installed
which claude  # or codex, gemini

# If not, install the corresponding agent
```
