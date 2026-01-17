# SSH Authentication with agbox: A Complete Guide to SSH Agent

## Why This Guide?

When using `agbox` to execute git operations (like `git fetch`, `git push`), you may encounter SSH authentication failures. This guide explains:
- How agbox affects SSH authentication
- Why SSH Agent is the more secure and recommended solution
- How to properly configure SSH Agent to resolve authentication issues

## SSH Basics

### SSH Key vs SSH Agent

**SSH Private Key**
- A private key file stored on disk (e.g., `~/.ssh/id_rsa`)
- SSH client reads this file for authentication on each connection
- Security risk: Any program with file read access can use your private key

**SSH Agent**
- A background process that manages your SSH keys
- Loads private keys into memory to avoid repeated password entry
- SSH client communicates with the agent via Unix socket to request signatures
- Security advantage: Private keys never leave the agent; only signatures are provided

### Advantages of SSH Agent

```
Traditional approach (direct key file access):
  SSH Client → Read ~/.ssh/id_rsa → Authenticate
  Problem: Any program can read the private key file

Using SSH Agent:
  SSH Client → Request signature via socket → SSH Agent → Sign with in-memory key → Return signature
  Advantage: Private key never leaves the agent; programs only get signatures
```

## agbox Default Behavior

`agbox` uses macOS sandbox to protect sensitive files. Here are the access rules for SSH-related files:

### Allowed Access ✅

```scheme
;; SSH Agent socket (for agent communication)
(allow file-read* file-write* file-ioctl
    (literal "/private/tmp/com.apple.launchd.XXX/Listeners"))

;; SSH basic files
(allow file-read*
    (literal "$HOME/.ssh")                  # SSH directory itself
    (literal "$HOME/.ssh/config")           # SSH config file
    (literal "$HOME/.ssh/known_hosts")      # Known hosts
    (regex #"$HOME/\.ssh/.*\.pub$"))        # Public key files
```

### Denied Access ❌

```scheme
;; SSH private keys (all non-public files are blocked)
(deny file-read* file-write*
    (subpath "$HOME/.ssh"))
```

This means:
- Programs inside `agbox` can communicate with SSH Agent
- Programs inside `agbox` cannot directly read SSH private key files

## Practical Demonstrations

The following demonstrations show the complete SSH authentication flow.

### Scenario 1: Clean Environment, Test Basic Authentication

> [!NOTE]
> **Scenario: Testing behavior without SSH keys**
>
> Goal: Understand how git operations behave inside agbox when SSH agent has no keys.

```bash
# 1. Remove all keys from SSH agent
$ ssh-add -D
All identities removed.

# 2. Confirm agent has no keys
$ ssh-add -l
The agent has no identities.

# 3. Test git fetch outside sandbox (should succeed, can read private key directly)
$ git fetch --dry-run
# No error messages

# 4. Test git fetch inside sandbox (will fail)
$ agbox git fetch
no such identity: $HOME/.ssh/user_github: Operation not permitted
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.
```

**Key Observations**:
- Outside sandbox: Success (SSH client can directly read private key files)
- Inside sandbox: Failure (private key files are blocked, and agent has no keys)

---

### Scenario 2: Adding Wrong Key (Key Without Repository Permission)

> [!NOTE]
> **Scenario: SSH agent has a key, but it lacks repository access**
>
> Goal: Understand the importance of key selection in the SSH authentication flow.

```bash
# 1. Add an SSH key to agent (but this key lacks GitHub repository permission)
$ ssh-add ~/.ssh/id_rsa
Identity added: $HOME/.ssh/id_rsa

# 2. Confirm keys in agent
$ ssh-add -l
2048 SHA256:xxxxx...xxxxx $HOME/.ssh/id_rsa (RSA)

# 3. Test git fetch inside sandbox (still fails)
$ agbox git fetch
no such identity: $HOME/.ssh/user_github: Operation not permitted
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.
```

**Why does it still fail?**

Use verbose mode to see the detailed process:

```bash
$ agbox ssh -vvv -T git@github.com 2>&1 | grep -E "Will attempt|Offering|Server accepts"

debug1: Will attempt key: $HOME/.ssh/id_rsa RSA SHA256:xxxxx agent
debug1: Will attempt key: $HOME/.ssh/user_github RSA SHA256:yyyyy explicit

debug1: Offering public key: $HOME/.ssh/id_rsa RSA SHA256:xxxxx agent
debug1: Authentications that can continue: publickey

debug1: Offering public key: $HOME/.ssh/user_github RSA SHA256:yyyyy explicit
debug1: Server accepts key: $HOME/.ssh/user_github RSA SHA256:yyyyy explicit

no such identity: $HOME/.ssh/user_github: Operation not permitted
```

**Authentication Flow Analysis**:
1. SSH first tries `id_rsa` from agent, but GitHub rejects it (key lacks permission)
2. SSH then tries `user_github` specified in SSH config
3. GitHub accepts the `user_github` key
4. SSH needs to sign with that key, but since it's not in agent, tries to read the file
5. File read is blocked by sandbox, authentication fails

---

### Scenario 3: Using SSH Agent (The Correct Approach) ✅

> [!NOTE]
> **Scenario: Add the correct key to SSH agent**
>
> Goal: Demonstrate the proper way to use SSH agent for secure and smooth SSH authentication.

```bash
# 1. Check your SSH config to find the IdentityFile used for GitHub
$ cat ~/.ssh/config
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/user_github

# 2. Add that key to SSH agent
$ ssh-add ~/.ssh/user_github
Identity added: $HOME/.ssh/user_github

# 3. Confirm keys in agent
$ ssh-add -l
2048 SHA256:xxxxx...xxxxx $HOME/.ssh/id_rsa (RSA)
2048 SHA256:yyyyy...yyyyy user_github (RSA)

# 4. Test SSH connection inside sandbox (Success!)
$ agbox ssh -T git@github.com
Hi username! You've successfully authenticated, but GitHub does not provide shell access.

# 5. Test git fetch inside sandbox (Success!)
$ agbox git fetch
# No error messages, executes normally

# 6. Test git clone, git push, etc. (All work)
$ agbox git clone git@github.com:user/repo.git
Cloning into 'repo'...
```

**Why does it succeed?**
- The correct key (`user_github`) is now in SSH agent
- SSH config requires `user_github`
- GitHub accepts this key
- SSH gets signature via agent socket (no need to read private key file)
- Sandbox allows agent socket access, authentication succeeds

---

### Scenario 4: Auto-load SSH Keys on Startup

> [!NOTE]
> **Scenario: Configure system to auto-load commonly used SSH keys**
>
> Goal: Avoid manually running `ssh-add` after every reboot.

Add the following to `~/.ssh/config`:

```ssh-config
Host *
    AddKeysToAgent yes
    UseKeychain yes
    IdentityFile ~/.ssh/user_github
    IdentityFile ~/.ssh/id_rsa
```

For macOS users, add keys to Keychain:

```bash
# Add key to agent and save to macOS Keychain
$ ssh-add --apple-use-keychain ~/.ssh/user_github
Enter passphrase for $HOME/.ssh/user_github:
Identity added: $HOME/.ssh/user_github

# After reboot, system will auto-load keys from Keychain
```

For Linux users, add to `~/.bashrc` or `~/.zshrc`:

```bash
# Auto-start ssh-agent and load keys on startup
if [ -z "$SSH_AUTH_SOCK" ]; then
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/user_github
fi
```

---

## Why Not Just Use `--allow-ssh-keys` Flag?

`agbox` provides the `--allow-ssh-keys` flag to relax SSH private key access restrictions:

```bash
$ agbox --allow-ssh-keys git fetch
```

This allows programs to directly read SSH private key files. While this solves the problem, it is **not recommended** because:

### Security Comparison

| Approach | Private Key Exposure | Security | Convenience |
|----------|---------------------|----------|-------------|
| **SSH Agent (Recommended)** | Keys only in agent memory, programs only get signatures | ✅ High | ✅ High (auto after setup) |
| **--allow-ssh-keys** | Allows programs to directly read private key files | ⚠️ Low | ✅ High (no setup needed) |

### Advantages of SSH Agent

1. **Principle of Least Privilege**: Programs can only get signatures, not private keys
2. **Industry Standard**: SSH agent is the standard practice in the SSH ecosystem
3. **Password Management**: Enter password once, agent handles subsequent authentications
4. **Cross-tool Support**: All SSH-based tools (git, rsync, scp) support it

### When Can You Use `--allow-ssh-keys`?

Consider using only in these situations:
- Debugging SSH-related issues
- Temporary needs in a known-safe environment
- Unable to use SSH agent (extremely rare)

For general use cases, SSH agent should be preferred.

---

## Troubleshooting

### Issue 1: `Could not open a connection to your authentication agent`

```bash
$ ssh-add -l
Could not open a connection to your authentication agent.
```

**Solution**: Start SSH agent

```bash
# Start ssh-agent
$ eval "$(ssh-agent -s)"
Agent pid 12345

# Try again
$ ssh-add -l
The agent has no identities.
```

---

### Issue 2: `Agent has no identities` but I'm sure I added keys before

```bash
$ ssh-add -l
The agent has no identities.
```

**Reason**: SSH agent is session-based; keys disappear after reboot or closing terminal.

**Solution**: See "Scenario 4: Auto-load SSH Keys on Startup" to configure auto-loading.

---

### Issue 3: Still getting `Operation not permitted` inside sandbox

```bash
$ agbox git fetch
no such identity: $HOME/.ssh/some_key: Operation not permitted
```

**Checklist**:

1. Confirm SSH agent is running:
   ```bash
   $ ssh-add -l
   ```

2. Confirm the required key is in agent:
   ```bash
   # Check IdentityFile required by SSH config
   $ cat ~/.ssh/config | grep -A 3 "Host github.com"

   # Add the corresponding key to agent
   $ ssh-add ~/.ssh/corresponding_key
   ```

3. Test if sandbox can access agent:
   ```bash
   $ agbox ssh-add -l
   ```

4. Use verbose mode to see detailed authentication flow:
   ```bash
   $ agbox ssh -vvv -T git@github.com 2>&1 | grep -E "Will attempt|Offering|Server accepts|identity"
   ```

---

### Issue 4: Different Git repositories need different SSH keys

**Scenario**: You have multiple GitHub accounts or different Git services (GitHub, GitLab, Bitbucket), each using different SSH keys.

**Solution**: Configure different Host aliases in `~/.ssh/config` for different services

```ssh-config
# Personal GitHub account
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/personal_github

# Work GitHub account
Host github-work
    HostName github.com
    User git
    IdentityFile ~/.ssh/work_github

# GitLab
Host gitlab.com
    HostName gitlab.com
    User git
    IdentityFile ~/.ssh/gitlab_key
```

Add all required keys to agent:

```bash
$ ssh-add ~/.ssh/personal_github
$ ssh-add ~/.ssh/work_github
$ ssh-add ~/.ssh/gitlab_key

$ ssh-add -l
2048 SHA256:xxxxx personal_github (RSA)
2048 SHA256:yyyyy work_github (RSA)
2048 SHA256:zzzzz gitlab_key (RSA)
```

Clone using the corresponding Host alias:

```bash
# Personal project
$ git clone git@github.com:personal/repo.git

# Work project
$ git clone git@github-work:company/repo.git
```

---

## Quick Reference

### Common Commands

```bash
# Check SSH agent status
ssh-add -l

# Add SSH key to agent
ssh-add ~/.ssh/your_key

# Add key and save to macOS Keychain
ssh-add --apple-use-keychain ~/.ssh/your_key

# Remove all keys from agent
ssh-add -D

# Test SSH connection
ssh -T git@github.com

# View detailed authentication process
ssh -vvv -T git@github.com

# Test SSH agent inside sandbox
agbox ssh-add -l

# Execute git operations inside sandbox
agbox git fetch
agbox git push
```

### Recommended Workflow

1. Auto-load SSH keys on system startup (configure Keychain or shell rc)
2. Use `agbox` for all git operations
3. No need to use `--allow-ssh-keys` flag
4. Enjoy secure and convenient SSH authentication

---

## Summary

- **Use SSH Agent**: This is the secure, standard, and recommended approach
- **Avoid Direct Key Access**: Using `--allow-ssh-keys` reduces security
- **Configure Auto-loading**: Let SSH agent auto-load commonly used keys on system startup
- **agbox Is Secure by Default**: Blocking private key access protects your credentials

When you properly configure SSH agent, all SSH-based operations inside `agbox` (git, scp, rsync) work smoothly while maintaining high security.
