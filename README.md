# Agent Sandbox

Sandbox wrapper for AI agents and automation tools using macOS Seatbelt, protecting sensitive files while allowing normal development workflow.

> [!IMPORTANT]
> **Personal Experimental Tool**
>
> This is a personal experimental sandbox tool customized for macOS use.
>
> - Relies on macOS Seatbelt (sandbox-exec), only works on macOS
> - Designed primarily for personal daily use, general-purpose applicability is still evolving
> - Feel free to fork or clone for your own use
> - Please evaluate risks before use; author makes no guarantees for all scenarios
>
> **SSH Usage Notes**
>
> - SSH private keys are blocked by default (unless using `--allow-ssh-keys`)
> - For Git operations, use SSH agent: `ssh-add ~/.ssh/your_key`
> - See [SSH Authentication Guide](README.ssh.md) for detailed setup and troubleshooting

## Features

### 🛡️ Three-Layer Security Architecture

1. **Common Rules** - Universal protection for sensitive files
   - SSH keys (`.ssh/`)
   - Cloud credentials (`.aws/`, `.gcloud/`, `.azure/`, `.kube/`)
   - GPG keys (`.gnupg/`)
   - Private keys (`*.pem`, `*.key`, `*_rsa`, etc.)
   - Environment files (`.env`, `.envrc`)

2. **Project Rules** - Workspace-specific configuration
   - Full read/write access in current working directory
   - Read-only access to Git config and Shell RC files
   - Python `__pycache__` writes
   - Temp directory access

3. **Agent-Specific Rules** - Per-agent configuration
   - Claude: `~/.claude/`
   - Codex: `~/.codex/`

### 🎯 Dynamic Working Directory

`agbox` dynamically generates sandbox profiles based on your current directory:
- Work in multiple projects simultaneously
- Each directory has independent write permissions
- No manual configuration needed

### ✅ Supported Agents

- **Claude Code** - AI coding assistant
- **Codex CLI** - AI coding assistant
- **Any command** - Generic sandbox support

## Installation

### Using pipx (Recommended)

```bash
pipx install agent-sandbox
```

### From Source

```bash
git clone https://github.com/qty-playground/agent-sandbox.git
cd agent-sandbox
pip install -e .
```

## Usage

### Basic Usage

```bash
# Navigate to your project
cd ~/projects/my-project

# Run Claude Code with sandbox
agbox claude

# Run Codex CLI with sandbox
agbox codex

# Run any command with sandbox
agbox python script.py
```

### Available Options

```bash
agbox [OPTIONS] [--] <command> [args...]

Options:
  --verbose              Show sandbox profile path and details
  --mode MODE            Security mode: strict, balanced, permissive (default: balanced)
  --agent AGENT          Agent type: claude, codex (auto-detected if omitted)
  --work-dir DIR         Working directory (default: current directory)
  --dry-run              Show profile content without executing
  --help                 Show this help message

Permission Flags:
  --allow-ssh-keys       Allow reading SSH private keys
  --allow-env-read       Allow reading environment files (.env, .envrc)
  --allow-aws-config     Allow reading AWS credentials
  --allow-cloud-config   Allow reading all cloud provider configs (AWS, GCP, Azure, k8s)
```

### Advanced Usage Examples

```bash
# Show sandbox details
agbox --verbose claude

# Use explicit separator for clarity
agbox --verbose -- claude --help

# Preview sandbox profile without executing
agbox --dry-run python script.py

# Explicitly specify agent type
agbox --agent claude /usr/local/bin/claude

# Use strict security mode
agbox --mode strict codex

# Run in specific working directory
agbox --work-dir ~/projects/other python test.py

# Grant temporary SSH key access (not recommended, use SSH agent instead)
agbox --allow-ssh-keys git clone git@github.com:user/repo.git

# Allow reading environment files
agbox --allow-env-read python script.py

# Combine multiple permission flags
agbox --allow-aws-config --allow-env-read python deploy.py
```

### Git Operations with SSH

For git operations with SSH authentication (clone, fetch, push), add your SSH key to ssh-agent:

```bash
# Add SSH key to agent
ssh-add ~/.ssh/your_key

# Verify key is loaded
ssh-add -l

# Now git operations work in sandbox
agbox git fetch
agbox git push
```

For detailed SSH setup, troubleshooting, and understanding why SSH agent is recommended over `--allow-ssh-keys`, see the [SSH Authentication Guide](README.ssh.md).

### Create Alias (Optional)

Add to `~/.zshrc` or `~/.bashrc`:

```bash
alias ab="agbox"
```

Then use:

```bash
cd ~/projects/my-project
ab claude
```

## How It Works

### Dynamic Sandbox Profile Generation

Each time you run `agbox`:

1. Detects current working directory (`pwd`)
2. Identifies agent type (claude, codex, or generic)
3. Dynamically generates sandbox profile with three layers:
   - Common security rules (SSH, GPG, cloud credentials)
   - Project rules (workspace access)
   - Agent-specific rules (tool configurations)
4. Executes command using `sandbox-exec`
5. Automatically cleans up temp file after exit

### Example Sandbox Profile Structure

```scheme
(version 1)
(allow default)  ; Default allow, protect via explicit deny

;; ========================================
;; COMMON: Sensitive file protection
;; ========================================
(deny file-read* file-write*
    (subpath "$HOME/.ssh"))

;; ========================================
;; PROJECT: Workspace and development tools
;; ========================================
(deny file-write*
    (subpath "$HOME"))

(allow file-write*
    (subpath "/path/to/current/project"))

;; ========================================
;; AGENT: Claude Code specific rules
;; ========================================
(allow file-write*
    (subpath "$HOME/.claude"))
```

## Verification

### Test SSH Protection

```bash
cd ~/projects/test
agbox --verbose claude

# In Claude, try to read SSH keys
# Should see "Operation not permitted"
```

### Test Working Directory Isolation

```bash
# Project A
cd ~/projects/project-a
agbox claude
# Claude can only write to ~/projects/project-a

# Project B
cd ~/projects/project-b
agbox codex
# Codex can only write to ~/projects/project-b
```

## Testing

This project includes automated pytest-based tests for validating agent functionality within the sandbox.

### Running Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run all tests (default: claude agent)
pytest tests/ -v

# Test specific agent
pytest tests/ --agent=claude -v
pytest tests/ --agent=codex -v
pytest tests/ --agent=gemini -v

# Quick test (skip slow tests)
make test-quick

# Using Makefile
make test           # Run tests with claude
make test-claude    # Run claude tests
make test-all       # Run tests for all agents
```

### Prerequisites for Tests

1. agbox must be installed and accessible in PATH
2. The agent you want to test must be installed
3. For git operation tests, SSH agent must be configured:
   ```bash
   ssh-add ~/.ssh/your_key
   ssh-add -l  # Verify key is loaded
   ```

### Test Coverage

The test suite covers all operations from `docs/test-plan.md`:

- TC-1: Agent launch and working directory access
- TC-2: File read operations
- TC-3: File write operations
- TC-4: File edit operations
- TC-5: Git branch creation and commits
- TC-6: Git branch switching
- TC-7: Git branch deletion
- TC-8: Script execution

For detailed testing documentation, see [tests/README.md](tests/README.md).

## Debugging

### Monitor Sandbox Violations

Use `agbox-debug` to monitor sandbox violations in real-time or review past logs:

```bash
# Live monitoring (Ctrl+C to stop)
agbox-debug

# Show denies from past 5 minutes
agbox-debug --last 5m

# Show all operations (allow + deny), not just denies
agbox-debug --all

# Past 1 hour, all operations
agbox-debug --last 1h --all
```

Run this in a separate terminal while testing agents. You'll see denied operations like:

```
Sandbox: cat(12345) deny(1) file-read-data /Users/you/.ssh/id_ed25519
Sandbox: python(12346) deny(1) file-write-data /Users/you/.bashrc
```

### View Generated Profile

Use `--dry-run` to preview the sandbox profile without executing:

```bash
agbox --dry-run claude
```

## Advanced Usage

### Adding Custom Agent Support

Edit `src/agent_sandbox/cli.py` to add your agent:

```python
def get_agent_rules(agent: str, home: Path) -> str:
    agent_configs = {
        'your-agent': f"""
;; Allow writing your agent config
(allow file-write*
    (subpath "{home}/.your-agent"))
""",
    }
    return agent_configs.get(agent, "")
```

## Requirements

- macOS (uses Seatbelt/Sandbox)
- Python 3.10+
- Tools you want to sandbox (claude, codex, etc.)

## Known Limitations

1. **macOS 14+ Limitations**: Uses `(allow default)` + explicit `deny` approach
2. **Symbolic Links**: Handling depends on target path resolution
3. **Relative Paths**: Sandbox rules use absolute paths

## Security Notes

1. Regularly review agent operation logs
2. Don't run unverified agents in sensitive project directories
3. Consider using `strict` mode for highly sensitive operations
4. Regularly update protection rules for new threats

## Contributing

Contributions welcome! Please open an issue or PR on [GitHub](https://github.com/qty-playground/agent-sandbox).

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Resources

- [macOS Sandbox Guide](https://reverse.put.as/wp-content/uploads/2011/09/Apple-Sandbox-Guide-v1.0.pdf)
- [Seatbelt Profiles](https://www.chromium.org/developers/design-documents/sandbox/osx-sandboxing-design/)
- [Claude Code Documentation](https://github.com/anthropics/claude-code)
- [Codex CLI Documentation](https://codex.storage.googleapis.com/agent/v0.38.1/docs.html)
