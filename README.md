# Agent Sandbox

Sandbox wrapper for AI agents and automation tools using macOS Seatbelt, protecting sensitive files while allowing normal development workflow.

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
```

### Git Operations with SSH

For `git push` to work, add your SSH key to ssh-agent:

```bash
# Add SSH key to agent
ssh-add ~/.ssh/id_ed25519

# Now git push works in sandbox
agbox claude
# (in Claude) git push
```

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
