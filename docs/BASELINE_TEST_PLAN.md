# Test Plan: Home Directory Access Baseline

> [!IMPORTANT]
> This manual test plan has been converted into automated pytest test cases. See `tests/test_agent_baseline.py` for the current implementation. This document is kept for reference and understanding the test objectives.

## Background

This test plan establishes a baseline for testing agbox functionality in a controlled environment. The goal is to ensure all core features work correctly, including agent launching and git operations with SSH authentication through ssh-agent.

## Test Environment Setup

### Location Structure
```
~/Downloads/agbox-labs/
└── <test-project>/          # Temporary directory for single test plan
    └── agent-sandbox/       # Cloned repository
```

### Test Project Naming Convention
- Format: `test-<feature>-<sequence>` or timestamp-based
- Example: `test-ban-home-001`, `test-ban-home-20260118-1430`

### Repository Setup
- Repository: `git@github.com:qty-playground/agent-sandbox.git`
- Access: Read/Write permissions available
- Clone method: `agbox git clone git@github.com:qty-playground/agent-sandbox.git`

### Test Branch Convention
- All test branches must use `test-` prefix
- Examples: `test-baseline-001`, `test-git-ops`

## Prerequisites

1. Choose which agent to test (one of: `claude`, `codex`, `gemini`)

2. SSH key must be loaded into ssh-agent for git operations (use `ssh-add ~/.ssh/your_key`)

3. agbox must be installed and accessible in PATH

4. The chosen agent must be installed and accessible in PATH

## Test Objectives

This baseline test ensures that all core operations work correctly in the agbox sandbox environment. This serves as a reference point for validating the current implementation and detecting regressions.

### Test Scope

1. **Agent Launch Test**: Verify the chosen agent can execute prompts in non-interactive mode without "Operation not permitted" errors
2. **File Operations Test**: Verify agent can read, write, and execute files in the working directory
3. **Git Operations Test**: Verify agent can perform git operations (local and remote) within the sandbox

## Test Cases

### TC-1: Agent Basic Launch and Working Directory Access

**Objective**: Verify that the chosen agent can launch and access the working directory without permission errors

**Procedure**:

First, verify the chosen agent is available:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
command -v <agent-name>
```

Then, execute the agent with a simple working directory query:

**For claude**:
```bash
# Claude uses -p flag for non-interactive output
agbox claude -p "what is the current working directory path?"
```

**For codex**:
```bash
# Codex uses exec command for non-interactive execution
agbox codex exec "what is the current working directory path?"
```

**For gemini**:
```bash
# Gemini uses positional prompt with -y flag for yolo mode
agbox gemini -y "what is the current working directory path?"
```

**Expected Result**:
- Agent executes successfully without entering interactive mode
- Agent returns the current working directory path (should contain `agbox-labs/<test-project>/agent-sandbox`)
- No "Operation not permitted" errors
- Clean exit after returning results

**Failure Criteria**:
- Any "Operation not permitted" error
- Agent fails to start or execute the prompt
- Agent cannot access working directory information
- Sandbox violation logs appear

---

### TC-2: File Read Operation

**Objective**: Verify agent can read files in the working directory

**Procedure**:

**For claude**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox claude -p "read the README.md file and tell me the project name"
```

**For codex**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox codex exec "read the README.md file and tell me the project name"
```

**For gemini**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox gemini -y "read the README.md file and tell me the project name"
```

**Expected Result**:
- Agent successfully reads README.md
- Agent returns the project name (should be "agent-sandbox" or similar)
- No "Operation not permitted" errors
- No file access denied errors

---

### TC-3: File Write Operation

**Objective**: Verify agent can create and write files in the working directory

**Procedure**:

**For claude**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox claude -p "create a new file called test-hello.txt with content 'Hello from agbox test'"
```

**For codex**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox codex exec "create a new file called test-hello.txt with content 'Hello from agbox test'"
```

**For gemini**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox gemini -y "create a new file called test-hello.txt with content 'Hello from agbox test'"
```

**Verify the file was created**:
```bash
cat test-hello.txt
```

**Expected Result**:
- Agent successfully creates test-hello.txt
- File contains the expected content
- No "Operation not permitted" errors
- No file write access denied errors

---

### TC-4: File Edit Operation

**Objective**: Verify agent can edit existing files in the working directory

**Procedure**:

**For claude**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox claude -p "edit test-hello.txt and append a new line 'Modified by agent'"
```

**For codex**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox codex exec "edit test-hello.txt and append a new line 'Modified by agent'"
```

**For gemini**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox gemini -y "edit test-hello.txt and append a new line 'Modified by agent'"
```

**Verify the file was modified**:
```bash
cat test-hello.txt
```

**Expected Result**:
- Agent successfully modifies test-hello.txt
- File contains both original content and the new line
- No "Operation not permitted" errors
- No file edit access denied errors

---

### TC-5: Git Branch Creation and Push

**Objective**: Verify agent can perform git operations (create branch, commit, push to remote)

**Procedure**:

**For claude**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox claude -p "create a new git branch called test-agent-branch, add the test-hello.txt file, commit with message 'test commit from agent', and push to remote"
```

**For codex**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox codex exec "create a new git branch called test-agent-branch, add the test-hello.txt file, commit with message 'test commit from agent', and push to remote"
```

**For gemini**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox gemini -y "create a new git branch called test-agent-branch, add the test-hello.txt file, commit with message 'test commit from agent', and push to remote"
```

**Verify the branch was created remotely**:
```bash
agbox git branch -r | grep test-agent-branch
```

**Expected Result**:
- Agent successfully creates local branch
- Agent successfully commits changes
- Agent successfully pushes to remote
- Remote branch is visible in branch list
- No "Operation not permitted" errors
- No SSH authentication errors (assumes ssh-agent is properly configured)

---

### TC-6: Git Pull Operation

**Objective**: Verify agent can pull latest changes from remote branch

**Procedure**:

**For claude**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox claude -p "switch to main branch and pull the latest changes from remote"
```

**For codex**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox codex exec "switch to main branch and pull the latest changes from remote"
```

**For gemini**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox gemini -y "switch to main branch and pull the latest changes from remote"
```

**Expected Result**:
- Agent successfully switches to main branch
- Agent successfully pulls from remote
- Working directory is updated with latest changes
- No "Operation not permitted" errors
- No SSH authentication errors

---

### TC-7: Git Branch Deletion (Local and Remote)

**Objective**: Verify agent can delete both local and remote branches

**Procedure**:

**For claude**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox claude -p "delete the test-agent-branch branch both locally and from remote origin"
```

**For codex**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox codex exec "delete the test-agent-branch branch both locally and from remote origin"
```

**For gemini**:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
agbox gemini -y "delete the test-agent-branch branch both locally and from remote origin"
```

**Verify the branch was deleted**:
```bash
agbox git branch -a | grep test-agent-branch
```

**Expected Result**:
- Agent successfully deletes remote branch
- Agent successfully deletes local branch
- grep returns no results (branch is completely removed)
- No "Operation not permitted" errors
- No SSH authentication errors

---

### TC-8: Script Execution

**Objective**: Verify agent can execute scripts in the working directory

**Procedure**:

First, create a test script:
```bash
cd ~/Downloads/agbox-labs/<test-project>/agent-sandbox
cat > test-script.sh << 'EOF'
#!/bin/bash
echo "Script executed successfully"
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -la
EOF
chmod +x test-script.sh
```

Then ask agent to execute it:

**For claude**:
```bash
agbox claude -p "run the test-script.sh script and show me the output"
```

**For codex**:
```bash
agbox codex exec "run the test-script.sh script and show me the output"
```

**For gemini**:
```bash
agbox gemini -y "run the test-script.sh script and show me the output"
```

**Expected Result**:
- Agent successfully executes the script
- Agent shows script output (including current directory and file list)
- No "Operation not permitted" errors
- No execution permission denied errors

---

## Test Execution Workflow

### 1. Environment Setup
```bash
# Choose which agent to test (one of: claude, codex, gemini)
export AGENT="claude"  # Change this to your chosen agent

# Verify agent is available
command -v $AGENT

# Create test project directory
mkdir -p ~/Downloads/agbox-labs
cd ~/Downloads/agbox-labs

# Generate test project name
TEST_PROJECT="test-baseline-$(date +%Y%m%d-%H%M%S)"
mkdir "$TEST_PROJECT"
cd "$TEST_PROJECT"

# Clone repository using agbox
agbox git clone git@github.com:qty-playground/agent-sandbox.git
cd agent-sandbox
```

### 2. Run All Test Cases

Choose the appropriate command pattern for your agent:

**For claude users**:
```bash
# TC-1: Basic launch and working directory access
agbox claude -p "what is the current working directory path?"

# TC-2: File read operation
agbox claude -p "read the README.md file and tell me the project name"

# TC-3: File write operation
agbox claude -p "create a new file called test-hello.txt with content 'Hello from agbox test'"

# TC-4: File edit operation
agbox claude -p "edit test-hello.txt and append a new line 'Modified by agent'"

# TC-5: Git branch creation and push
agbox claude -p "create a new git branch called test-agent-branch, add the test-hello.txt file, commit with message 'test commit from agent', and push to remote"

# TC-6: Git pull operation
agbox claude -p "switch to main branch and pull the latest changes from remote"

# TC-7: Git branch deletion
agbox claude -p "delete the test-agent-branch branch both locally and from remote origin"

# TC-8: Script execution
cat > test-script.sh << 'EOF'
#!/bin/bash
echo "Script executed successfully"
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -la
EOF
chmod +x test-script.sh
agbox claude -p "run the test-script.sh script and show me the output"
```

**For codex users**:
```bash
# TC-1: Basic launch and working directory access
agbox codex exec "what is the current working directory path?"

# TC-2: File read operation
agbox codex exec "read the README.md file and tell me the project name"

# TC-3: File write operation
agbox codex exec "create a new file called test-hello.txt with content 'Hello from agbox test'"

# TC-4: File edit operation
agbox codex exec "edit test-hello.txt and append a new line 'Modified by agent'"

# TC-5: Git branch creation and push
agbox codex exec "create a new git branch called test-agent-branch, add the test-hello.txt file, commit with message 'test commit from agent', and push to remote"

# TC-6: Git pull operation
agbox codex exec "switch to main branch and pull the latest changes from remote"

# TC-7: Git branch deletion
agbox codex exec "delete the test-agent-branch branch both locally and from remote origin"

# TC-8: Script execution
cat > test-script.sh << 'EOF'
#!/bin/bash
echo "Script executed successfully"
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -la
EOF
chmod +x test-script.sh
agbox codex exec "run the test-script.sh script and show me the output"
```

**For gemini users**:
```bash
# TC-1: Basic launch and working directory access
agbox gemini -y "what is the current working directory path?"

# TC-2: File read operation
agbox gemini -y "read the README.md file and tell me the project name"

# TC-3: File write operation
agbox gemini -y "create a new file called test-hello.txt with content 'Hello from agbox test'"

# TC-4: File edit operation
agbox gemini -y "edit test-hello.txt and append a new line 'Modified by agent'"

# TC-5: Git branch creation and push
agbox gemini -y "create a new git branch called test-agent-branch, add the test-hello.txt file, commit with message 'test commit from agent', and push to remote"

# TC-6: Git pull operation
agbox gemini -y "switch to main branch and pull the latest changes from remote"

# TC-7: Git branch deletion
agbox gemini -y "delete the test-agent-branch branch both locally and from remote origin"

# TC-8: Script execution
cat > test-script.sh << 'EOF'
#!/bin/bash
echo "Script executed successfully"
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -la
EOF
chmod +x test-script.sh
agbox gemini -y "run the test-script.sh script and show me the output"
```

### 3. Cleanup
```bash
# Clean up test files created during testing
cd ~/Downloads/agbox-labs/"$TEST_PROJECT"/agent-sandbox
rm -f test-hello.txt test-script.sh

# Switch back to main branch
agbox git checkout main

# Leave test project directory
cd ~

# Optional: Remove test project directory after verification
rm -rf ~/Downloads/agbox-labs/"$TEST_PROJECT"
```

## Success Criteria

All test cases must pass with:
- Zero "Operation not permitted" errors
- Zero sandbox violation logs
- All git operations complete successfully
- No unexpected errors or warnings

## Failure Analysis

If any test case fails:

### For "Operation not permitted" errors:
1. Check `agbox-debug` output for sandbox violations
2. Check current sandbox profile rules with `agbox --dry-run <agent>`
3. Document the specific file path or operation that was denied

### For SSH/Git authentication errors:
1. Verify SSH key is loaded: `ssh-add -l`
2. Test SSH connection outside sandbox: `ssh -T git@github.com`
3. Test SSH connection inside sandbox: `agbox ssh -T git@github.com`
4. Check if SSH_AUTH_SOCK is properly passed to sandbox

### For agent execution errors:
1. Test the same prompt outside sandbox to verify it works
2. Check agent-specific error messages (API errors, rate limits, etc.)
3. Try with verbose/debug mode if available
4. Verify agent has access to required tools (Bash, Edit, Write, etc.)

### For file operation errors:
1. Verify working directory permissions: `ls -la`
2. Check if files already exist (for create operations)
3. Check if files are readable/writable outside sandbox first
4. Document the specific file operation that failed

## Notes

- This baseline test establishes expected behavior for the current implementation
- Results serve as reference point for validating changes and detecting regressions
- All operations are performed through agents to simulate real development workflow
- Test covers both file operations and git operations to ensure complete agent functionality
- All test branches and files should be cleaned up after testing
- Document any unexpected behavior or edge cases discovered during testing

## Daily Development Workflow Simulation

This test plan is designed to simulate a typical daily development workflow:

1. **Start working**: Agent can access and understand the working directory (TC-1)
2. **Read code**: Agent can read existing project files (TC-2)
3. **Write code**: Agent can create new files (TC-3)
4. **Modify code**: Agent can edit existing files (TC-4)
5. **Version control**: Agent can create branches, commit, and push changes (TC-5)
6. **Sync with team**: Agent can pull latest changes (TC-6)
7. **Clean up**: Agent can delete branches after work is done (TC-7)
8. **Run tasks**: Agent can execute build/test scripts (TC-8)

If all test cases pass, the agent should be able to handle most daily development tasks within the agbox sandbox environment.
