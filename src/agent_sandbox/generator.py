#!/usr/bin/env python3
"""
Sandbox Profile Generator for AI Agents and Automation Tools
Usage: generate-sandbox-profile [options]
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import List


class SandboxProfileGenerator:
    """Sandbox Profile Generator for macOS Seatbelt"""

    MODES = ['strict', 'balanced', 'permissive']

    def __init__(self, output_file: str, mode: str, work_dir: str, allowed_paths: List[str],
                 allow_git: bool = False, allow_rc_read: bool = False, allow_env_read: bool = False):
        self.output_file = Path(output_file).expanduser()
        self.mode = mode
        self.work_dir = Path(work_dir).expanduser().resolve()
        self.allowed_paths = [Path(p).expanduser().resolve() for p in allowed_paths]
        self.home = Path.home()
        self.allow_git = allow_git
        self.allow_rc_read = allow_rc_read
        self.allow_env_read = allow_env_read

    def generate_base_rules(self) -> str:
        """Generate base rules"""
        return f"""(version 1)

;; ========================================
;; Default allow all operations (protect via explicit deny)
;; Note: (deny default) may have limitations on macOS 14+
;; ========================================
(allow default)
"""

    def generate_sensitive_protection_rules(self) -> str:
        """Generate sensitive file protection rules (applied to all modes)"""
        rules = ["""
;; ========================================
;; Sensitive file protection (applied to all modes)
;; ========================================

;; Deny SSH keys (always protected)
(deny file-read* file-write*
    (subpath "{home}/.ssh"))

;; Deny cloud service credentials (always protected)
(deny file-read* file-write*
    (subpath "{home}/.aws")
    (subpath "{home}/.azure")
    (subpath "{home}/.gcloud")
    (subpath "{home}/.kube"))

;; Deny GPG keys (always protected)
(deny file-read* file-write*
    (subpath "{home}/.gnupg"))
""".format(home=self.home)]

        # Shell RC file protection
        if self.allow_rc_read:
            rules.append(f"""
;; Allow reading Shell RC files (but deny writes)
(allow file-read*
    (literal "{self.home}/.bashrc")
    (literal "{self.home}/.bash_profile")
    (literal "{self.home}/.bash_login")
    (literal "{self.home}/.profile")
    (literal "{self.home}/.zshrc")
    (literal "{self.home}/.zshenv")
    (literal "{self.home}/.zprofile")
    (literal "{self.home}/.zlogin")
    (literal "{self.home}/.tcshrc")
    (literal "{self.home}/.cshrc"))

(deny file-write*
    (literal "{self.home}/.bashrc")
    (literal "{self.home}/.bash_profile")
    (literal "{self.home}/.bash_login")
    (literal "{self.home}/.profile")
    (literal "{self.home}/.zshrc")
    (literal "{self.home}/.zshenv")
    (literal "{self.home}/.zprofile")
    (literal "{self.home}/.zlogin")
    (literal "{self.home}/.tcshrc")
    (literal "{self.home}/.cshrc"))
""")
        else:
            rules.append(f"""
;; Deny Shell RC files (prevent command injection)
(deny file-read* file-write*
    (literal "{self.home}/.bashrc")
    (literal "{self.home}/.bash_profile")
    (literal "{self.home}/.bash_login")
    (literal "{self.home}/.profile")
    (literal "{self.home}/.zshrc")
    (literal "{self.home}/.zshenv")
    (literal "{self.home}/.zprofile")
    (literal "{self.home}/.zlogin")
    (literal "{self.home}/.tcshrc")
    (literal "{self.home}/.cshrc"))
""")

        # Environment file protection
        if self.allow_env_read:
            rules.append(f"""
;; Allow reading environment files (but deny writes)
(allow file-read*
    (literal "{self.home}/.env")
    (literal "{self.home}/.envrc")
    (regex #"{self.home}/\\.env\\..*$"))

(deny file-write*
    (literal "{self.home}/.env")
    (literal "{self.home}/.envrc")
    (regex #"{self.home}/\\.env\\..*$"))
""")
        else:
            rules.append(f"""
;; Deny environment files
(deny file-read* file-write*
    (literal "{self.home}/.env")
    (literal "{self.home}/.envrc")
    (regex #"{self.home}/\\.env\\..*$"))
""")

        # Git credential protection
        if self.allow_git:
            rules.append(f"""
;; Allow reading Git config (but deny writes)
(allow file-read*
    (literal "{self.home}/.gitconfig")
    (literal "{self.home}/.git-credentials")
    (literal "{self.home}/.netrc"))

(deny file-write*
    (literal "{self.home}/.gitconfig")
    (literal "{self.home}/.git-credentials")
    (literal "{self.home}/.netrc"))
""")
        else:
            rules.append(f"""
;; Deny Git credentials
(deny file-read* file-write*
    (literal "{self.home}/.gitconfig")
    (literal "{self.home}/.git-credentials")
    (literal "{self.home}/.netrc"))
""")

        # Private key file protection (always protected)
        rules.append(f"""
;; Deny private key files (always protected)
(deny file-read* file-write*
    (regex #"{self.home}/.*\\.pem$")
    (regex #"{self.home}/.*\\.key$")
    (regex #"{self.home}/.*\\.p12$")
    (regex #"{self.home}/.*\\.pfx$")
    (regex #"{self.home}/.*_rsa$")
    (regex #"{self.home}/.*_dsa$")
    (regex #"{self.home}/.*_ecdsa$")
    (regex #"{self.home}/.*_ed25519$"))

;; Deny credential/password files
(deny file-read* file-write*
    (regex #"{self.home}/[^/]*credentials$")
    (regex #"{self.home}/[^/]*password[^/]*$")
    (regex #"{self.home}/\\..*credentials$")
    (regex #"{self.home}/\\..*token$")
    (regex #"{self.home}/\\..*secret$"))
""")

        return "".join(rules)

    def generate_strict_rules(self) -> str:
        """Generate strict mode rules"""
        return f"""
;; ========================================
;; STRICT MODE: Deny writes outside working directory
;; ========================================

;; Allow reading .local directory (tools and applications)
(allow file-read*
    (subpath "{self.home}/.local"))

;; Deny writes to home directory (except working directory)
(deny file-write*
    (subpath "{self.home}")
    (subpath "/"))

;; Allow writing working directory
(allow file-write*
    (subpath "{self.work_dir}"))

;; Allow Python __pycache__ writes
(allow file-write*
    (regex #"{self.home}/\\.local/.*/__pycache__/.*")
    (regex #"{self.home}/miniforge3/.*/__pycache__/.*")
    (regex #"{self.home}/\\.pyenv/.*/__pycache__/.*")
    (regex #".*/__pycache__/.*\\.pyc$"))

;; Allow /tmp writes
(allow file-write*
    (subpath "/tmp")
    (subpath "/var/tmp")
    (subpath "/private/tmp"))
"""

    def generate_balanced_rules(self) -> str:
        """Generate balanced mode rules"""
        return f"""
;; ========================================
;; BALANCED MODE: Deny writes to most of home directory
;; ========================================

;; Allow reading .local directory (tools and applications)
(allow file-read*
    (subpath "{self.home}/.local"))

;; Deny writes to home directory (except working directory)
(deny file-write*
    (subpath "{self.home}"))

;; Allow writing working directory
(allow file-write*
    (subpath "{self.work_dir}"))

;; Allow Python __pycache__ writes
(allow file-write*
    (regex #"{self.home}/\\.local/.*/__pycache__/.*")
    (regex #"{self.home}/miniforge3/.*/__pycache__/.*")
    (regex #"{self.home}/\\.pyenv/.*/__pycache__/.*")
    (regex #".*/__pycache__/.*\\.pyc$"))

;; Allow /tmp writes
(allow file-write*
    (subpath "/tmp")
    (subpath "/var/tmp")
    (subpath "/private/tmp"))
"""

    def generate_permissive_rules(self) -> str:
        """Generate permissive mode rules"""
        return f"""
;; ========================================
;; PERMISSIVE MODE: Relaxed restrictions (sensitive files still protected)
;; ========================================

;; Most operations are allowed in this mode
;; Only sensitive files are protected (see protection rules below)
"""

    def generate_custom_paths_rules(self) -> str:
        """Generate custom path rules"""
        if not self.allowed_paths:
            return ""

        rules = ["""
;; ========================================
;; User-defined allowed paths
;; ========================================"""]

        for path in self.allowed_paths:
            rules.append(f"""(allow file-read* file-write*
    (subpath "{path}"))""")

        return "\n".join(rules)

    def generate(self) -> str:
        """Generate complete profile"""
        parts = [self.generate_base_rules()]

        # Generate rules based on mode
        if self.mode == 'strict':
            parts.append(self.generate_strict_rules())
        elif self.mode == 'balanced':
            parts.append(self.generate_balanced_rules())
        elif self.mode == 'permissive':
            parts.append(self.generate_permissive_rules())

        # Custom path rules
        custom_rules = self.generate_custom_paths_rules()
        if custom_rules:
            parts.append(custom_rules)

        # Add sensitive file protection last (highest priority, overrides previous allow rules)
        parts.append(self.generate_sensitive_protection_rules())

        return "\n".join(parts)

    def validate_syntax(self) -> bool:
        """Validate profile syntax"""
        try:
            result = subprocess.run(
                ['sandbox-exec', '-f', str(self.output_file), '/bin/echo', 'syntax check'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def save(self) -> None:
        """Save profile to file"""
        profile_content = self.generate()

        # Ensure directory exists
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        self.output_file.write_text(profile_content)

        # Set permissions
        self.output_file.chmod(0o644)

    def print_summary(self) -> None:
        """Print summary information"""
        print(f"\nGenerating Sandbox Profile...")
        print(f"  Mode: {self.mode}")
        print(f"  Working directory: {self.work_dir}")
        print(f"  Output file: {self.output_file}")
        if self.allowed_paths:
            print(f"  Additional paths: {', '.join(str(p) for p in self.allowed_paths)}")

        print(f"\n  Always protected:")
        print(f"    - SSH keys (.ssh/)")
        print(f"    - Cloud credentials (.aws/, .gcloud/, .azure/, .kube/)")
        print(f"    - GPG keys (.gnupg/)")
        print(f"    - Private key files (*.pem, *.key, *_rsa, etc.)")

        print(f"\n  Conditional protection:")
        if self.allow_git:
            print(f"    - Git config: Allow read (--allow-git)")
        else:
            print(f"    - Git config: Fully denied")

        if self.allow_rc_read:
            print(f"    - Shell RC files: Allow read (--allow-rc-read)")
        else:
            print(f"    - Shell RC files: Fully denied")

        if self.allow_env_read:
            print(f"    - Environment files: Allow read (--allow-env-read)")
        else:
            print(f"    - Environment files: Fully denied")

    def print_usage_instructions(self) -> None:
        """Print usage instructions"""
        print(f"\n✓ Profile generated: {self.output_file}\n")
        print("Usage:")
        print(f'  sandbox-exec -f "{self.output_file}" <command>\n')
        print("Examples:")
        print(f'  sandbox-exec -f "{self.output_file}" claude --dangerously-skip-permissions')
        print(f'  sandbox-exec -f "{self.output_file}" aider')
        print(f'  agbox claude  # Using agbox wrapper (recommended)')
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Sandbox Profile Generator for AI Agents and Automation Tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Mode descriptions:
  strict      - Read-only, writes limited to working directory
  balanced    - Allow reading most system files, writes limited to working directory
  permissive  - Relaxed restrictions, but still protects sensitive directories

Examples:
  %(prog)s -m strict -w ~/projects/myapp
  %(prog)s -m balanced -a /usr/local/bin -a ~/Documents
  %(prog)s -o /tmp/custom-sandbox.sb -m permissive
        """
    )

    parser.add_argument(
        '-o', '--output',
        default='~/.agent-sandbox.sb',
        help='Output file path (default: ~/.agent-sandbox.sb)'
    )

    parser.add_argument(
        '-m', '--mode',
        choices=SandboxProfileGenerator.MODES,
        default='balanced',
        help='Security mode (default: balanced)'
    )

    parser.add_argument(
        '-w', '--work-dir',
        default=os.getcwd(),
        help='Working directory (default: current directory)'
    )

    parser.add_argument(
        '-a', '--allow',
        action='append',
        default=[],
        dest='allowed_paths',
        help='Additional allowed paths (repeatable)'
    )

    parser.add_argument(
        '--allow-git',
        action='store_true',
        help='Allow reading Git config (.gitconfig, .git-credentials) - but deny writes'
    )

    parser.add_argument(
        '--allow-rc-read',
        action='store_true',
        help='Allow reading Shell RC files (.bashrc, .zshrc, etc.) - but deny writes'
    )

    parser.add_argument(
        '--allow-env-read',
        action='store_true',
        help='Allow reading environment files (.env, .envrc) - but deny writes'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show profile content only, do not write to file'
    )

    args = parser.parse_args()

    # Validate working directory
    work_dir = Path(args.work_dir).expanduser()
    if not work_dir.exists():
        print(f"Warning: Working directory does not exist: {work_dir}", file=sys.stderr)
        response = input("Continue anyway? (y/N) ").strip().lower()
        if response not in ('y', 'yes'):
            sys.exit(1)

    # Create generator
    generator = SandboxProfileGenerator(
        output_file=args.output,
        mode=args.mode,
        work_dir=args.work_dir,
        allowed_paths=args.allowed_paths,
        allow_git=args.allow_git,
        allow_rc_read=args.allow_rc_read,
        allow_env_read=args.allow_env_read
    )

    # Dry run mode
    if args.dry_run:
        print("=== Profile Content ===")
        print(generator.generate())
        return

    # Generate and save
    generator.print_summary()
    generator.save()

    # Validate syntax
    print("\nValidating profile syntax...")
    if generator.validate_syntax():
        print("✓ Profile syntax is valid")
        generator.print_usage_instructions()
        print("All set!")
    else:
        print("⚠ Profile may have syntax errors, please check", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
