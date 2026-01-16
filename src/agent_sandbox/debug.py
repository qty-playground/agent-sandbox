#!/usr/bin/env python3
"""
Agent Sandbox Debug Tool
Monitor sandbox violations in real-time or review past logs
"""

import sys
import subprocess
from typing import Optional


def print_usage(error_msg: Optional[str] = None):
    """Print usage information"""
    if error_msg:
        print(f"Error: {error_msg}\n", file=sys.stderr)

    print("Usage: agbox-debug [OPTIONS]", file=sys.stderr)
    print("\nMonitor sandbox violations for debugging agent behavior", file=sys.stderr)
    print("\nOptions:", file=sys.stderr)
    print("  --last TIME    Show past logs (e.g., 5m, 1h, 2d) instead of live stream", file=sys.stderr)
    print("  --all          Show all operations (allow + deny), not just denies", file=sys.stderr)
    print("  --help         Show this help message", file=sys.stderr)
    print("\nExamples:", file=sys.stderr)
    print("  agbox-debug                 # Live monitoring (Ctrl+C to stop)", file=sys.stderr)
    print("  agbox-debug --last 5m       # Show denies from past 5 minutes", file=sys.stderr)
    print("  agbox-debug --all           # Live, show all operations", file=sys.stderr)
    print("  agbox-debug --last 1h --all # Past 1 hour, all operations", file=sys.stderr)
    print("\nTip: Run this in a separate terminal while testing agents", file=sys.stderr)

    sys.exit(1 if error_msg else 0)


def parse_args(args: list[str]) -> dict:
    """Parse command line arguments"""
    options = {
        'last': None,
        'all': False,
    }

    i = 0
    while i < len(args):
        arg = args[i]

        if arg in ('--help', '-h'):
            print_usage()

        elif arg == '--last':
            if i + 1 >= len(args):
                print_usage("--last requires an argument")
            options['last'] = args[i + 1]
            i += 2

        elif arg == '--all':
            options['all'] = True
            i += 1

        else:
            print_usage(f"Unknown option: {arg}")

    return options


def watch_sandbox_logs(show_all: bool = False, last: Optional[str] = None):
    """
    Watch sandbox violations in real-time or show past logs

    Args:
        show_all: If True, show all sandbox operations (allow + deny)
        last: If set, show past logs (e.g., '5m', '1h', '2d') instead of streaming
    """
    # Build predicate
    if show_all:
        predicate = 'eventMessage CONTAINS "Sandbox"'
    else:
        predicate = 'eventMessage CONTAINS "Sandbox" AND eventMessage CONTAINS "deny"'

    # Build command
    if last:
        # Show past logs
        cmd = [
            '/usr/bin/log', 'show',
            '--predicate', predicate,
            '--last', last,
            '--style', 'syslog'
        ]
        print(f"Showing sandbox {'operations' if show_all else 'denies'} from past {last}...")
    else:
        # Stream live logs
        cmd = [
            '/usr/bin/log', 'stream',
            '--predicate', predicate,
            '--style', 'syslog'
        ]
        print(f"Watching sandbox {'operations' if show_all else 'denies'} (Ctrl+C to stop)...")

    print()

    try:
        # Execute log command
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\nStopped watching.")
        sys.exit(0)


def main():
    """CLI entry point"""
    options = parse_args(sys.argv[1:])
    watch_sandbox_logs(show_all=options['all'], last=options['last'])


if __name__ == '__main__':
    main()
