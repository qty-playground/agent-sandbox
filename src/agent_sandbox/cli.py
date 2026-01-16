#!/usr/bin/env python3
"""
Agent Sandbox CLI
Dynamically generate sandbox profile and execute AI agents or automation tools
"""

import sys
import os
import subprocess
import tempfile
import shutil
import shlex
from pathlib import Path
from typing import List, Dict, Tuple, Optional


def get_common_rules(home: Path) -> str:
    """
    Common security rules applied to all agents
    Protects sensitive files: SSH keys, cloud credentials, GPG, etc.
    """
    ssh_auth_sock = os.environ.get('SSH_AUTH_SOCK', '')
    ssh_agent_rule = ""
    if ssh_auth_sock:
        ssh_agent_rule = f"""
;; Allow SSH Agent access (for git push)
(allow file-read* file-write* file-ioctl
    (literal "{ssh_auth_sock}"))
"""

    return f"""{ssh_agent_rule}
;; ========================================
;; COMMON: Sensitive file protection
;; ========================================

;; Deny SSH directory (protect all private keys and sensitive files)
(deny file-read* file-write*
    (subpath "{home}/.ssh"))

;; Allow reading safe SSH files and configs
(allow file-read*
    (literal "{home}/.ssh")
    (literal "{home}/.ssh/config")
    (literal "{home}/.ssh/known_hosts")
    (literal "{home}/.ssh/known_hosts.old")
    (regex #"{home}/\\.ssh/.*\\.pub$"))

;; Deny cloud service credentials (always protected)
(deny file-read* file-write*
    (subpath "{home}/.aws")
    (subpath "{home}/.azure")
    (subpath "{home}/.gcloud")
    (subpath "{home}/.kube"))

;; Deny GPG keys (always protected)
(deny file-read* file-write*
    (subpath "{home}/.gnupg"))

;; Deny environment variable files in home
(deny file-read* file-write*
    (literal "{home}/.env")
    (literal "{home}/.envrc")
    (regex #"{home}/\\.env\\..*$"))

;; Deny private key files (always protected)
(deny file-read* file-write*
    (regex #"{home}/[^/]*\\.pem$")
    (regex #"{home}/[^/]*-key\\.pem$")
    (regex #"{home}/[^/]*_key\\.pem$")
    (regex #"{home}/[^/]*\\.key$")
    (regex #"{home}/[^/]*\\.p12$")
    (regex #"{home}/[^/]*\\.pfx$")
    (regex #"{home}/.*_rsa$")
    (regex #"{home}/.*_dsa$")
    (regex #"{home}/.*_ecdsa$")
    (regex #"{home}/.*_ed25519$"))

;; Deny credential/password files
(deny file-read* file-write*
    (regex #"{home}/[^/]*credentials$")
    (regex #"{home}/[^/]*password[^/]*$")
    (regex #"{home}/\\..*credentials$")
    (regex #"{home}/\\..*token$")
    (regex #"{home}/\\..*secret$"))
"""


def get_project_rules(work_dir: Path, home: Path) -> str:
    """
    Project-specific rules
    Controls workspace access and common development needs
    """
    return f"""
;; ========================================
;; PROJECT: Workspace and development tools
;; ========================================

;; Allow reading .local directory (tools and applications)
(allow file-read*
    (subpath "{home}/.local"))

;; Deny writes to home directory (except specific allowed paths)
(deny file-write*
    (subpath "{home}"))

;; Allow writing current working directory
(allow file-write*
    (subpath "{work_dir}"))

;; Allow Python __pycache__ writes
(allow file-write*
    (regex #"{home}/\\.local/.*/__pycache__/.*")
    (regex #"{home}/miniforge3/.*/__pycache__/.*")
    (regex #"{home}/\\.pyenv/.*/__pycache__/.*")
    (regex #".*/__pycache__/.*\\.pyc$"))

;; Allow /tmp writes
(allow file-write*
    (subpath "/tmp")
    (subpath "/var/tmp")
    (subpath "/private/tmp"))

;; Allow common shell tool caches and temporary files
(allow file-write*
    (subpath "{home}/.cache")
    (subpath "{home}/.config")
    (regex #"{home}/\\.zcompdump.*$"))

;; Allow reading Shell RC files (but deny writes)
(allow file-read*
    (literal "{home}/.bashrc")
    (literal "{home}/.bash_profile")
    (literal "{home}/.bash_login")
    (literal "{home}/.profile")
    (literal "{home}/.zshrc")
    (literal "{home}/.zshenv")
    (literal "{home}/.zprofile")
    (literal "{home}/.zlogin")
    (literal "{home}/.tcshrc")
    (literal "{home}/.cshrc"))

(deny file-write*
    (literal "{home}/.bashrc")
    (literal "{home}/.bash_profile")
    (literal "{home}/.bash_login")
    (literal "{home}/.profile")
    (literal "{home}/.zshrc")
    (literal "{home}/.zshenv")
    (literal "{home}/.zprofile")
    (literal "{home}/.zlogin")
    (literal "{home}/.tcshrc")
    (literal "{home}/.cshrc"))

;; Allow reading Git config (but deny writes)
(allow file-read*
    (literal "{home}/.gitconfig")
    (literal "{home}/.git-credentials")
    (literal "{home}/.netrc"))

(deny file-write*
    (literal "{home}/.gitconfig")
    (literal "{home}/.git-credentials")
    (literal "{home}/.netrc"))
"""


def get_agent_rules(agent: str, home: Path) -> str:
    """
    Common agent configuration rules
    Always allow writes to common AI agent directories
    """
    return f"""
;; ========================================
;; AGENTS: Common AI agent config directories
;; ========================================

;; Allow writing Claude Code config
(allow file-write*
    (literal "{home}/.claude.json")
    (subpath "{home}/.claude")
    (subpath "{home}/.config/claude-code"))

;; Allow writing Codex CLI config
(allow file-write*
    (subpath "{home}/.codex"))
"""


def generate_sandbox_profile(work_dir: Path, home: Path, agent: str = "") -> str:
    """
    Dynamically generate sandbox profile combining three layers:
    1. Common security rules (sensitive file protection)
    2. Project rules (workspace access)
    3. Agent-specific rules (tool configurations)
    """
    return f"""(version 1)

;; ========================================
;; Default allow all operations (protect via explicit deny)
;; ========================================
(allow default)
{get_common_rules(home)}
{get_project_rules(work_dir, home)}
{get_agent_rules(agent, home)}
"""


def print_usage(error_msg: Optional[str] = None):
    """Print usage information"""
    if error_msg:
        print(f"Error: {error_msg}\n", file=sys.stderr)

    print("Usage: agbox [OPTIONS] [--] <command> [args...]", file=sys.stderr)
    print("\nOptions:", file=sys.stderr)
    print("  --verbose              Show sandbox profile path and details", file=sys.stderr)
    print("  --mode MODE            Security mode: strict, balanced, permissive (default: balanced)", file=sys.stderr)
    print("  --agent AGENT          Agent type: claude, codex (auto-detected if omitted)", file=sys.stderr)
    print("  --work-dir DIR         Working directory (default: current directory)", file=sys.stderr)
    print("  --dry-run              Show profile content without executing", file=sys.stderr)
    print("  --help                 Show this help message", file=sys.stderr)
    print("\nExamples:", file=sys.stderr)
    print("  agbox claude                      # Run Claude Code", file=sys.stderr)
    print("  agbox codex                       # Run Codex CLI", file=sys.stderr)
    print("  agbox my_alias                    # Run shell alias (auto-detected)", file=sys.stderr)
    print("  agbox --verbose claude            # Show details", file=sys.stderr)
    print("  agbox --dry-run python test.py    # Show profile only", file=sys.stderr)
    print("\nNote: If command is not found, agbox will automatically try to execute it as a shell alias.", file=sys.stderr)
    print("\nDebug tool:", file=sys.stderr)
    print("  agbox-debug                       # Monitor sandbox violations", file=sys.stderr)

    sys.exit(1 if error_msg else 0)


def parse_args(args: List[str]) -> Tuple[Dict[str, any], List[str]]:
    """
    Parse command line arguments with smart detection

    Returns: (agbox_options, command_args)

    Examples:
        agbox claude           -> ({}, ['claude', '--dangerously-skip-permissions'])
        agbox --verbose aider  -> ({'verbose': True}, ['aider'])
        agbox -- python test.py -> ({}, ['python', 'test.py'])
    """
    options = {
        'verbose': False,
        'mode': 'balanced',
        'agent': None,
        'work_dir': None,
        'dry_run': False,
    }

    i = 0
    while i < len(args):
        arg = args[i]

        # Explicit separator: everything after is command
        if arg == '--':
            cmd_args = args[i + 1:]
            break

        # Help
        elif arg in ('--help', '-h'):
            print_usage()

        # Verbose
        elif arg == '--verbose':
            options['verbose'] = True
            i += 1

        # Mode
        elif arg == '--mode':
            if i + 1 >= len(args):
                print_usage("--mode requires an argument")
            options['mode'] = args[i + 1]
            if options['mode'] not in ('strict', 'balanced', 'permissive'):
                print_usage(f"Invalid mode: {options['mode']}")
            i += 2

        # Agent
        elif arg == '--agent':
            if i + 1 >= len(args):
                print_usage("--agent requires an argument")
            options['agent'] = args[i + 1]
            i += 2

        # Work directory
        elif arg == '--work-dir':
            if i + 1 >= len(args):
                print_usage("--work-dir requires an argument")
            options['work_dir'] = args[i + 1]
            i += 2

        # Dry run
        elif arg == '--dry-run':
            options['dry_run'] = True
            i += 1

        # Unknown option
        elif arg.startswith('-'):
            print_usage(f"Unknown option: {arg}")

        # First non-option argument: start of command
        else:
            cmd_args = args[i:]
            break
    else:
        # No command found
        cmd_args = []

    # Command is required
    if not cmd_args:
        print_usage("No command specified")

    # Detect agent if not specified
    if not options['agent'] and cmd_args:
        known_agents = ['claude', 'codex']
        cmd_name = cmd_args[0]
        if cmd_name in known_agents:
            options['agent'] = cmd_name

    # Special case: claude without args -> add --dangerously-skip-permissions
    if options['agent'] == 'claude' and len(cmd_args) == 1:
        cmd_args.append('--dangerously-skip-permissions')

    return options, cmd_args


def main():
    """CLI entry point"""
    # Parse arguments
    options, cmd_args = parse_args(sys.argv[1:])

    # Get directories
    work_dir = Path(options['work_dir']).resolve() if options['work_dir'] else Path.cwd().resolve()
    home = Path.home()

    # Generate sandbox profile
    profile_content = generate_sandbox_profile(work_dir, home, options['agent'] or '')

    # Dry run mode
    if options['dry_run']:
        print("=== Sandbox Profile ===")
        print(f"Working directory: {work_dir}")
        print(f"Agent: {options['agent'] or 'generic'}")
        print(f"Mode: {options['mode']}")
        print()
        print(profile_content)
        return

    # Create temporary file to store profile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sb', delete=False) as f:
        profile_path = f.name
        f.write(profile_content)

    try:
        # Auto-detect if command needs shell execution (for aliases)
        # Check if command exists as executable
        if not shutil.which(cmd_args[0]):
            # Command not found in PATH, might be alias/function
            # Use interactive shell to execute
            shell = os.environ.get('SHELL', '/bin/bash')
            cmd_string = ' '.join(shlex.quote(arg) for arg in cmd_args)
            cmd_args = [shell, '-i', '-c', cmd_string]

        # Show information if verbose
        if options['verbose']:
            print(f"Working directory: {work_dir}")
            print(f"Agent: {options['agent'] or 'generic'}")
            print(f"Mode: {options['mode']}")
            print(f"Sandbox Profile: {profile_path}")
            print(f"Command: {' '.join(cmd_args)}")
            print()

        # Build sandbox-exec command
        cmd = ['sandbox-exec', '-f', profile_path] + cmd_args

        # Execute and wait for completion
        result = subprocess.run(cmd)
        sys.exit(result.returncode)

    finally:
        # Cleanup temporary file
        try:
            os.unlink(profile_path)
        except:
            pass


if __name__ == '__main__':
    main()
