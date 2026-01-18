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

### 🛡️ Security Model

Deny-by-default approach: only explicitly allowed operations and paths are permitted.

**Dot-file Protection**
- All dot-files and dot-directories in home are denied by default
- Only explicitly allowed items can be accessed
- Development tools (`.m2`, `.gradle`, `.npm`, `.cargo`, `.pyenv`, etc.) are read-only
- Agent directories (`.claude`, `.codex`) have read/write access

**Sensitive Files (always denied)**
- SSH keys (`.ssh/`)
- Cloud credentials (`.aws/`, `.gcloud/`, `.azure/`, `.kube/`)
- GPG keys (`.gnupg/`)
- Private keys (`*.pem`, `*.key`, `*_rsa`, etc.)
- Credential/password/token/secret files
- Environment files (`.env`, `.envrc`)

**Project Access**
- Full read/write access in current working directory
- Write access limited to work directory, temp directories, and specific cache locations
- Shell RC files (`.bashrc`, `.zshrc`, etc.) are read-only
- Git config files are read-only

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

1. Detects current working directory
2. Identifies agent type (claude, codex, or generic)
3. Dynamically generates sandbox profile:
   - Deny-by-default baseline
   - Sensitive file protection
   - Dot-file protection with allowed exceptions
   - Work directory access
   - Agent-specific configurations
4. Executes command using `sandbox-exec`
5. Automatically cleans up temp file after exit

### Sandbox Profile Structure

The generated profile uses macOS Seatbelt syntax with a deny-by-default approach:

- Denies all operations by default
- Allows specific system operations (process, network, etc.)
- Denies all dot-files in home directory
- Explicitly allows needed development tools (read-only)
- Allows work directory (read/write)
- Allows agent config directories (read/write)

Use `agbox --dry-run <command>` to view the full generated profile.

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

Pytest-based automated tests cover:

- TC-1: Agent launch and working directory access
- TC-2: File read operations
- TC-3: File write operations
- TC-4: File edit operations
- TC-5: Git branch creation and commits
- TC-6: Git branch switching
- TC-7: Git branch deletion
- TC-8: Script execution
- Sensitive file protection (SSH keys, cloud credentials, GPG keys, etc.)
- Conditional protection (shell RC files, environment files, git config)

**Note**: Tests interact with actual AI agents. Results may vary depending on agent behavior and response quality.

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

Edit `src/agent_sandbox/cli.py` in the `get_agent_rules()` function to add your agent:

```python
def get_agent_rules(agent: str, home: Path) -> str:
    """Allow read and write access to AI agent directories"""
    return f"""
;; Allow your agent config (read and write)
(allow file-read* file-write*
    (subpath "{home}/.your-agent"))
"""
```

## Requirements

- macOS (uses Seatbelt/Sandbox)
- Python 3.10+
- Tools you want to sandbox (claude, codex, etc.)

## Known Limitations

1. **macOS Only**: Relies on macOS Seatbelt (sandbox-exec)
2. **Symbolic Links**: Handling depends on target path resolution
3. **Relative Paths**: Sandbox rules use absolute paths

## Security Notes

1. Uses deny-by-default model for defense in depth
2. All dot-files in home directory are blocked by default
3. Sensitive files (SSH keys, cloud credentials, GPG keys) are always protected
4. Use `agbox-debug` to monitor sandbox violations in real-time

## Contributing

Contributions welcome! Please open an issue or PR on [GitHub](https://github.com/qty-playground/agent-sandbox).

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Resources

- [macOS Sandbox Guide](https://reverse.put.as/wp-content/uploads/2011/09/Apple-Sandbox-Guide-v1.0.pdf)
- [Seatbelt Profiles](https://www.chromium.org/developers/design-documents/sandbox/osx-sandboxing-design/)
- [Claude Code Documentation](https://github.com/anthropics/claude-code)
- [Codex CLI Documentation](https://codex.storage.googleapis.com/agent/v0.38.1/docs.html)
