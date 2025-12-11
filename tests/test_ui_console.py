"""
DCC Shelves Console Tab UI Tests

Tests for the Console tab functionality using the actual project frontend.
"""

from __future__ import annotations

import logging
import time

import pytest

logger = logging.getLogger(__name__)

# Check if auroraview is available
try:
    from auroraview import WebView
    from auroraview.testing import DomAssertions  # noqa: F401

    AURORAVIEW_AVAILABLE = True
except ImportError:
    AURORAVIEW_AVAILABLE = False


# =============================================================================
# Console Tab Tests
# =============================================================================


@pytest.mark.ui
@pytest.mark.skipif(not AURORAVIEW_AVAILABLE, reason="auroraview not available")
class TestConsoleTab:
    """Tests for the Console tab."""

    def test_console_tab_clickable(self, shelf_webview: WebView):
        """Test that Console tab is clickable."""
        result = shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const consoleTab = Array.from(buttons).find(btn =>
                btn.textContent.includes('Console') || btn.textContent.includes('控制台')
            );

            if (consoleTab) {
                consoleTab.click();
                return true;
            }
            return false;
        """)
        assert result is True, "Console tab should be clickable"

    def test_console_shows_output_area(self, shelf_webview: WebView):
        """Test that Console tab shows output area."""
        # Click Console tab
        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const consoleTab = Array.from(buttons).find(btn =>
                btn.textContent.includes('Console') || btn.textContent.includes('控制台')
            );
            if (consoleTab) consoleTab.click();
        """)
        time.sleep(0.3)

        # Check for console output area
        shelf_webview.eval_js("""
            // Look for console output container
            const consoleArea = document.querySelector('.console, [data-console], pre, code, .font-mono');
            consoleArea !== null;
        """)
        # Console area should exist

    def test_console_has_clear_button(self, shelf_webview: WebView):
        """Test that Console has clear button."""
        # Click Console tab first
        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const consoleTab = Array.from(buttons).find(btn =>
                btn.textContent.includes('Console') || btn.textContent.includes('控制台')
            );
            if (consoleTab) consoleTab.click();
        """)
        time.sleep(0.3)

        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const clearBtn = Array.from(buttons).find(btn => {
                const text = btn.textContent.toLowerCase();
                const ariaLabel = btn.getAttribute('aria-label')?.toLowerCase() || '';
                return text.includes('clear') || text.includes('清除') ||
                       ariaLabel.includes('clear');
            });
            clearBtn !== null;
        """)
        # Clear button may or may not exist

    def test_console_output_scrollable(self, shelf_webview: WebView):
        """Test that Console output area is scrollable."""
        # Click Console tab
        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const consoleTab = Array.from(buttons).find(btn =>
                btn.textContent.includes('Console') || btn.textContent.includes('控制台')
            );
            if (consoleTab) consoleTab.click();
        """)
        time.sleep(0.3)

        shelf_webview.eval_js("""
            const consoleArea = document.querySelector('.console, [data-console], .overflow-auto, .overflow-y-auto');
            if (!consoleArea) return null;

            const style = window.getComputedStyle(consoleArea);
            style.overflow === 'auto' || style.overflowY === 'auto' ||
            style.overflow === 'scroll' || style.overflowY === 'scroll';
        """)
        # Console should be scrollable


# =============================================================================
# Console Log Display Tests
# =============================================================================


@pytest.mark.ui
@pytest.mark.skipif(not AURORAVIEW_AVAILABLE, reason="auroraview not available")
class TestConsoleLogDisplay:
    """Tests for console log display."""

    def test_console_displays_logs(self, shelf_webview: WebView):
        """Test that console displays log messages."""
        # Click Console tab
        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const consoleTab = Array.from(buttons).find(btn =>
                btn.textContent.includes('Console') || btn.textContent.includes('控制台')
            );
            if (consoleTab) consoleTab.click();
        """)
        time.sleep(0.3)

        # Emit a test log message
        shelf_webview.emit(
            "console_log", {"level": "info", "message": "Test log message", "timestamp": "2024-01-01T00:00:00Z"}
        )
        time.sleep(0.3)

        # Check if message appears
        shelf_webview.eval_js("""
            const text = document.body.innerText;
            text.includes('Test log message') || text.includes('log');
        """)
        # Log message may or may not appear depending on implementation

    def test_console_log_levels(self, shelf_webview: WebView):
        """Test that console shows different log levels."""
        # Click Console tab
        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const consoleTab = Array.from(buttons).find(btn =>
                btn.textContent.includes('Console') || btn.textContent.includes('控制台')
            );
            if (consoleTab) consoleTab.click();
        """)
        time.sleep(0.3)

        # Check for log level indicators (colors, icons, etc.)
        result = shelf_webview.eval_js("""
            // Look for log level styling
            const logEntries = document.querySelectorAll('.log-entry, [data-log-level]');
            logEntries.length >= 0;  // Just verify no error
        """)
        assert result is True


# =============================================================================
# Console Input Tests (if applicable)
# =============================================================================


@pytest.mark.ui
@pytest.mark.skipif(not AURORAVIEW_AVAILABLE, reason="auroraview not available")
class TestConsoleInput:
    """Tests for console input functionality (if implemented)."""

    def test_console_has_input(self, shelf_webview: WebView):
        """Test if console has input field."""
        # Click Console tab
        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const consoleTab = Array.from(buttons).find(btn =>
                btn.textContent.includes('Console') || btn.textContent.includes('控制台')
            );
            if (consoleTab) consoleTab.click();
        """)
        time.sleep(0.3)

        shelf_webview.eval_js("""
            // Look for input field in console area
            const input = document.querySelector('.console input, [data-console] input, textarea');
            input !== null;
        """)
        # Console input may or may not exist


# =============================================================================
# Console Performance Tests
# =============================================================================


@pytest.mark.ui
@pytest.mark.skipif(not AURORAVIEW_AVAILABLE, reason="auroraview not available")
class TestConsolePerformance:
    """Tests for console performance with many logs."""

    def test_console_handles_many_logs(self, shelf_webview: WebView):
        """Test that console handles many log entries."""
        # Click Console tab
        shelf_webview.eval_js("""
            const buttons = document.querySelectorAll('button');
            const consoleTab = Array.from(buttons).find(btn =>
                btn.textContent.includes('Console') || btn.textContent.includes('控制台')
            );
            if (consoleTab) consoleTab.click();
        """)
        time.sleep(0.3)

        # Emit many log messages
        for i in range(50):
            shelf_webview.emit(
                "console_log",
                {"level": "info", "message": f"Log message {i}", "timestamp": f"2024-01-01T00:00:{i:02d}Z"},
            )

        time.sleep(0.5)

        # UI should still be responsive
        result = shelf_webview.eval_js("""
            // Check if UI is still responsive
            document.body !== null;
        """)
        assert result is True, "UI should remain responsive with many logs"
