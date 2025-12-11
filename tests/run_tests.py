#!/usr/bin/env python
"""
DCC Shelves UI Test Runner

This script runs the UI tests using the actual project frontend.
It can start the Vite dev server automatically if needed.

Usage:
    # Run all tests
    python tests/run_tests.py

    # Run specific test file
    python tests/run_tests.py -k test_ui_main_layout

    # Run with verbose output
    python tests/run_tests.py -v

    # Run only layout tests
    python tests/run_tests.py --layout

    # Run with dev server auto-start
    python tests/run_tests.py --start-server
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def is_dev_server_running() -> bool:
    """Check if Vite dev server is running."""
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("localhost", 5173))
        sock.close()
        return result == 0
    except Exception:
        return False


def start_dev_server() -> subprocess.Popen | None:
    """Start Vite dev server."""
    print("Starting Vite dev server...")
    process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    )

    # Wait for server to start
    for i in range(30):
        if is_dev_server_running():
            print(f"Dev server started (took {i + 1}s)")
            return process
        time.sleep(1)
        print(".", end="", flush=True)

    print("\nFailed to start dev server")
    process.terminate()
    return None


def main():
    parser = argparse.ArgumentParser(description="Run DCC Shelves UI tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-k", "--keyword", type=str, help="Run tests matching keyword")
    parser.add_argument("--layout", action="store_true", help="Run only layout tests")
    parser.add_argument("--interactions", action="store_true", help="Run only interaction tests")
    parser.add_argument("--dialogs", action="store_true", help="Run only dialog tests")
    parser.add_argument("--console", action="store_true", help="Run only console tests")
    parser.add_argument("--i18n", action="store_true", help="Run only i18n tests")
    parser.add_argument("--start-server", action="store_true", help="Auto-start dev server")
    parser.add_argument("--no-server-check", action="store_true", help="Skip server check")
    args = parser.parse_args()

    # Check/start dev server
    dev_process = None
    if not args.no_server_check and not is_dev_server_running():
        if args.start_server:
            dev_process = start_dev_server()
            if not dev_process:
                print("Error: Could not start dev server")
                return 1
        else:
            # Check if dist exists
            dist_dir = PROJECT_ROOT / "dist"
            if not (dist_dir / "index.html").exists():
                print("Warning: Dev server not running and dist not built.")
                print("Run 'npm run dev' or 'npm run build' first, or use --start-server")
                return 1

    # Build pytest command
    pytest_args = [
        sys.executable,
        "-m",
        "pytest",
        str(PROJECT_ROOT / "tests"),
        "-v" if args.verbose else "-q",
        "--tb=short",
    ]

    # Add keyword filter
    if args.keyword:
        pytest_args.extend(["-k", args.keyword])
    elif args.layout:
        pytest_args.extend(["-k", "test_ui_main_layout"])
    elif args.interactions:
        pytest_args.extend(["-k", "test_ui_interactions"])
    elif args.dialogs:
        pytest_args.extend(["-k", "test_ui_dialogs"])
    elif args.console:
        pytest_args.extend(["-k", "test_ui_console"])
    elif args.i18n:
        pytest_args.extend(["-k", "test_ui_i18n"])

    try:
        print(f"\nRunning: {' '.join(pytest_args)}\n")
        result = subprocess.run(pytest_args, cwd=str(PROJECT_ROOT))
        return result.returncode
    finally:
        # Cleanup dev server if we started it
        if dev_process:
            print("\nStopping dev server...")
            dev_process.terminate()
            dev_process.wait(timeout=5)


if __name__ == "__main__":
    sys.exit(main())
