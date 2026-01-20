# Agent Sandbox Testing Prompt

This is a standard workflow for testing whether a new agent works correctly in the sandbox environment. Follow these steps when you need to validate agent compatibility with agbox.

## Testing Objective

Verify that an agent can run normally in the sandbox environment and fix any permission-related issues.

## Testing Workflow

### 1. Launch agbox-debug Monitoring

Start agbox-debug in the background to monitor sandbox violations in real-time:

```bash
agbox-debug &
```

This creates a background task that continuously monitors and logs all sandbox violation events.

### 2. Execute Agent Test

Launch the agent with agbox using a simple test command:

```bash
agbox <agent-command> -p "simple test instruction"
```

Examples:
- `agbox c4d -p "hello, please respond with one sentence"`
- `agbox gemini -y -p "read the first 10 lines of README.md in current directory"`
- `agbox codex -p "run python --version"`

### 3. Check Test Results

Observe two aspects:

1. **Agent Output**: Did the agent start successfully and respond normally?
2. **Error Messages**: Are there any permission-related errors?

Common permission error message patterns:
- `Error: EPERM: operation not permitted, open '...'`
- `PermissionError: [Errno 1] Operation not permitted: '...'`

### 4. Analyze agbox-debug Output

If permission errors are found, check the agbox-debug output:

```bash
# View recent violation records
tail -100 <agbox-debug-output-file> | grep -E "(deny|agent-name)"

# Or watch live output
tail -f <agbox-debug-output-file>
```

Focus on:
- `deny(1) file-read-*` - Read access blocked
- `deny(1) file-write-*` - Write access blocked
- Blocked file paths

### 5. Fix Permission Issues

Based on violation records from agbox-debug, add corresponding permissions in `src/agent_sandbox/cli.py`.

#### 5.1 Determine Permission Type

Identify required permissions:
- **Read-only**: Configuration files, config directories (readonly)
- **Read-write**: Log files, cache, state files

#### 5.2 Choose Appropriate Section

Add agent-specific permissions in the `get_agent_rules()` function:

```python
def get_agent_rules(agent: str, home: Path) -> str:
    """
    Common agent configuration rules
    """
    return f"""
;; Allow <Agent Name> config (read and write)
(allow file-read* file-write*
    (subpath "{{home}}/.agent-config-dir"))
"""
```

Common permission patterns:

**A. Agent Config Directory (read-write)**
```scheme
;; Allow <Agent> config (read and write)
(allow file-read* file-write*
    (subpath "{home}/.agent-dir"))
```

**B. Specific Config Files (read-write)**
```scheme
(allow file-read* file-write*
    (literal "{home}/.agent-config.json")
    (literal "{home}/.agent-config.lock"))
```

**C. Development Tool Directory (read-only)**
In the development tools section of `generate_sandbox_profile()`:
```scheme
;; ALLOWED: Development tool directories (read-only)
(allow file-read*
    (literal "{home}/.tool-config"))
```

**D. Cache/Metadata (read-write)**
In the cache section:
```scheme
;; ALLOWED: Cache and config directories (read-write)
(allow file-read* file-write*
    (subpath "{home}/.tool/metadata"))
```

#### 5.3 Path Pattern Guidelines

| Path Type | Use | Example |
|-----------|-----|---------|
| Single file | `(literal "path")` | `.condarc`, `.claude.json.lock` |
| Entire directory | `(subpath "path")` | `.claude/`, `.gemini/` |
| Pattern matching | `(regex #"pattern")` | `\\.zcompdump.*$` |

### 6. Retest

After fixing, re-run the test command from step 2 to confirm:
1. Agent works normally
2. agbox-debug no longer shows related violations

### 7. Commit Changes

Once tests pass, create a commit:

```bash
git add src/agent_sandbox/cli.py
git commit -m "Add <agent-name> permissions

- Add <file/directory> read/write access
- Fixes: <description of issue resolved>
"
git push
```

## Common Troubleshooting

### Q1: Agent starts but shows warnings

Check file paths mentioned in warning messages - may be non-critical config files being blocked. Evaluate whether permissions need to be added.

### Q2: Cannot find agbox-debug output file

When agbox-debug runs as a background task, output is written to `/var/folders/.../tasks/<task-id>.output`. Use `jobs` or check background task messages to find the file path.

### Q3: Unsure whether to use literal or subpath

- Single file → `literal`
- Entire directory and its contents → `subpath`
- Regular filename patterns → `regex`

## Testing Examples

### Example 1: Testing Claude Code (c4d)

```bash
# 1. Start monitoring
agbox-debug &

# 2. Test
agbox c4d -p "hello"

# 3. Error found: Cannot write .claude.json.lock
# 4. Check agbox-debug:
#    Sandbox: node deny(1) file-write-create /Users/xxx/.claude.json.lock

# 5. Fix: Add to get_agent_rules()
(allow file-read* file-write*
    (literal "{home}/.claude.json.lock"))

# 6. Retest → Success
```

### Example 2: Testing Gemini CLI

```bash
# 1. Start monitoring
agbox-debug &

# 2. Test
agbox gemini -y -p "hello"

# 3. Error found: EPERM: operation not permitted, open '.gemini/settings.json'

# 4. Fix: Add to get_agent_rules()
(allow file-read* file-write*
    (subpath "{home}/.gemini"))

# 5. Retest → Success
```

## Important Notes

1. **Principle of Least Privilege**: Only grant necessary permissions, prefer `literal` over `subpath`
2. **Distinguish Read/Write**: Config files usually only need read, logs/cache need write
3. **Thorough Testing**: Test not just startup, but main agent functions (read files, write files, execute commands, etc.)
4. **Record Violations**: Keep agbox-debug output for reference
5. **Version Control**: Each fix should be an independent commit for easy tracking and rollback
