"""Command-line entry point for AuroraView DCC Shelves.

This module provides a CLI interface for running the shelf as a standalone
desktop application. It can be invoked in several ways:

    # As a module
    python -m auroraview_dcc_shelves --config shelf_config.yaml

    # With the installed command (after pip install)
    auroraview-shelves --config shelf_config.yaml

    # Short alias
    dcc-shelves --config shelf_config.yaml

Usage:
    auroraview-shelves [OPTIONS]

Options:
    -c, --config PATH    Path to YAML configuration file
    -d, --debug          Enable debug mode with developer tools
    -w, --width INT      Window width (default: 800)
    -h, --height INT     Window height (default: 600)
    -t, --title TEXT     Window title (default: "DCC Shelves")
    --help               Show this help message

Examples:
    # Run with a configuration file
    auroraview-shelves -c examples/shelf_config.yaml

    # Run in debug mode
    auroraview-shelves -c shelf_config.yaml --debug

    # Custom window size
    auroraview-shelves -c shelf_config.yaml -w 1024 -h 768
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="auroraview-shelves",
        description="AuroraView DCC Shelves - A dynamic tool shelf system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -c shelf_config.yaml
  %(prog)s -c examples/shelf_config.yaml --debug
  %(prog)s -c config.yaml -w 1024 -h 768 -t "My Tools"

For more information, visit:
  https://github.com/loonghao/auroraview-dcc-shelves
        """,
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        metavar="PATH",
        help="Path to YAML configuration file",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug mode with developer tools (F12 or right-click)",
    )

    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=0,
        metavar="INT",
        help="Window width in pixels (default: 800)",
    )

    parser.add_argument(
        "--height",
        type=int,
        default=0,
        metavar="INT",
        help="Window height in pixels (default: 600)",
    )

    parser.add_argument(
        "-t",
        "--title",
        type=str,
        default="DCC Shelves",
        metavar="TEXT",
        help="Window title (default: DCC Shelves)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )

    return parser


def get_version() -> str:
    """Get the package version.

    Returns:
        Version string.
    """
    try:
        from auroraview_dcc_shelves import __version__

        return __version__
    except ImportError:
        return "unknown"


def find_config_file(config_path: str | None) -> str | None:
    """Find and validate the configuration file path.

    Searches for the configuration file in common locations:
    1. Exact path provided
    2. Current working directory
    3. Examples directory (for development)

    Args:
        config_path: User-provided config path, or None.

    Returns:
        Resolved path to configuration file, or None if not found.
    """
    if config_path:
        path = Path(config_path)
        if path.exists():
            return str(path.resolve())

        # Try current directory
        cwd_path = Path.cwd() / config_path
        if cwd_path.exists():
            return str(cwd_path.resolve())

        logger.error(f"Configuration file not found: {config_path}")
        return None

    # Look for default config files
    default_names = [
        "shelf_config.yaml",
        "shelf_config.yml",
        "shelves.yaml",
        "shelves.yml",
        "config.yaml",
        "config.yml",
    ]

    # Check current directory
    for name in default_names:
        path = Path.cwd() / name
        if path.exists():
            logger.info(f"Found configuration file: {path}")
            return str(path.resolve())

    # Check examples directory (for development)
    examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
    if examples_dir.exists():
        for name in default_names:
            path = examples_dir / name
            if path.exists():
                logger.info(f"Found example configuration: {path}")
                return str(path.resolve())

    return None


def main(args: list[str] | None = None) -> int:
    """Main entry point for the CLI.

    Args:
        args: Command-line arguments. If None, uses sys.argv.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    # Configure logging level
    if parsed_args.verbose or parsed_args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Find configuration file
    config_path = find_config_file(parsed_args.config)

    if config_path is None and parsed_args.config:
        # User specified a config but it wasn't found
        logger.error(
            f"Configuration file not found: {parsed_args.config}\n"
            "Please provide a valid path to a YAML configuration file."
        )
        return 1

    if config_path is None:
        logger.info(
            "No configuration file specified. "
            "Use -c/--config to specify a configuration file, "
            "or create a shelf_config.yaml in the current directory."
        )
        # Continue with empty config - will show empty shelf

    logger.info("Starting AuroraView DCC Shelves in desktop mode...")

    try:
        from auroraview_dcc_shelves.apps.desktop import run_desktop

        return run_desktop(
            config_path=config_path,
            debug=parsed_args.debug,
            width=parsed_args.width,
            height=parsed_args.height,
            title=parsed_args.title,
        )
    except ImportError as e:
        logger.error(
            f"Failed to import required modules: {e}\n"
            "Make sure auroraview is installed with Qt support:\n"
            "  pip install auroraview-dcc-shelves[qt]"
        )
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
