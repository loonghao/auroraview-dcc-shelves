"""Nox sessions for auroraview-dcc-shelves."""

from pathlib import Path

import nox

# Project configuration
PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"

# Default sessions
nox.options.sessions = ["lint", "pytest"]


@nox.session(python=["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"])
def pytest(session: nox.Session) -> None:
    """Run unit tests with pytest."""
    session.install(".[dev]")
    session.run("pytest", *session.posargs)


@nox.session
def lint(session: nox.Session) -> None:
    """Run code quality checks with ruff."""
    session.install("ruff")
    session.run("ruff", "check", str(SRC_DIR), str(TESTS_DIR))
    session.run("ruff", "format", "--check", str(SRC_DIR), str(TESTS_DIR))


@nox.session
def format(session: nox.Session) -> None:
    """Format code with ruff."""
    session.install("ruff")
    session.run("ruff", "check", "--fix", str(SRC_DIR), str(TESTS_DIR))
    session.run("ruff", "format", str(SRC_DIR), str(TESTS_DIR))


@nox.session
def coverage(session: nox.Session) -> None:
    """Generate test coverage report."""
    session.install(".[dev]")
    session.run(
        "pytest",
        "--cov=src/auroraview_dcc_shelves",
        "--cov-report=html",
        "--cov-report=term-missing",
        *session.posargs,
    )

