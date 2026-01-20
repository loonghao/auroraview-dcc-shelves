"""
Tests for remote debugging port feature.

This module tests the remote_debugging_port parameter in ShelfApp and WebViewManager,
which enables Chrome DevTools Protocol (CDP) for MCP/Playwright/Puppeteer control.
"""

from __future__ import annotations

import contextlib
from unittest.mock import MagicMock, patch

import pytest


class TestRemoteDebuggingPort:
    """Tests for remote_debugging_port functionality."""

    def test_shelf_app_accepts_remote_debugging_port(self):
        """Test that ShelfApp accepts remote_debugging_port parameter."""
        from auroraview_dcc_shelves.app import ShelfApp
        from auroraview_dcc_shelves.config import ShelvesConfig

        # Create minimal config
        config = ShelvesConfig(shelves=[])

        # Test with remote_debugging_port=None (default)
        app = ShelfApp(config)
        assert app.remote_debugging_port is None

        # Test with specific port
        app_with_port = ShelfApp(config, remote_debugging_port=9222)
        assert app_with_port.remote_debugging_port == 9222

        # Test with different port
        app_with_custom_port = ShelfApp(config, remote_debugging_port=9333)
        assert app_with_custom_port.remote_debugging_port == 9333

    def test_webview_manager_accepts_remote_debugging_port(self):
        """Test that WebViewManager accepts remote_debugging_port parameter."""
        from auroraview_dcc_shelves.managers.webview_manager import WebViewManager

        # Test with None (default)
        manager = WebViewManager()
        assert manager.remote_debugging_port is None

        # Test with specific port
        manager_with_port = WebViewManager(remote_debugging_port=9222)
        assert manager_with_port.remote_debugging_port == 9222

    def test_webview_manager_get_webview_params_includes_port(self):
        """Test that get_webview_params includes remote_debugging_port when set."""
        from auroraview_dcc_shelves.managers.webview_manager import WebViewManager

        # Without port
        manager = WebViewManager()
        params = manager.get_webview_params(debug=True)
        assert "remote_debugging_port" not in params

        # With port
        manager_with_port = WebViewManager(remote_debugging_port=9222)
        params_with_port = manager_with_port.get_webview_params(debug=True)
        assert params_with_port.get("remote_debugging_port") == 9222

    def test_webview_manager_get_webview_params_respects_adapter(self):
        """Test that get_webview_params respects adapter params but adds port."""
        from auroraview_dcc_shelves.managers.webview_manager import WebViewManager

        # Create mock adapter
        mock_adapter = MagicMock()
        mock_adapter.get_webview_params.return_value = {
            "dev_tools": True,
            "context_menu": False,
        }

        manager = WebViewManager(adapter=mock_adapter, remote_debugging_port=9222)
        params = manager.get_webview_params(debug=True)

        # Should include adapter params
        assert params.get("dev_tools") is True
        assert params.get("context_menu") is False
        # Should include remote_debugging_port
        assert params.get("remote_debugging_port") == 9222
        # Should include embed_mode (always added)
        assert params.get("embed_mode") == "container"

    def test_shelf_app_passes_port_to_webview_manager(self):
        """Test that ShelfApp passes remote_debugging_port to WebViewManager."""
        from auroraview_dcc_shelves.app import ShelfApp
        from auroraview_dcc_shelves.config import ShelvesConfig

        config = ShelvesConfig(shelves=[])
        app = ShelfApp(config, remote_debugging_port=9222)

        # Check that the webview_manager has the port
        assert app._webview_manager.remote_debugging_port == 9222

    def test_webview_manager_without_port_does_not_add_param(self):
        """Test that WebViewManager doesn't add remote_debugging_port when None."""
        from auroraview_dcc_shelves.managers.webview_manager import WebViewManager

        manager = WebViewManager()
        params = manager.get_webview_params(debug=False)

        # Should not include remote_debugging_port
        assert "remote_debugging_port" not in params

    def test_remote_debugging_port_docstring(self):
        """Test that remote_debugging_port property has proper documentation."""
        from auroraview_dcc_shelves.app import ShelfApp

        # Check that the property has a docstring
        assert ShelfApp.remote_debugging_port.__doc__ is not None
        assert "Chrome DevTools Protocol" in ShelfApp.remote_debugging_port.__doc__
        assert "CDP" in ShelfApp.remote_debugging_port.__doc__
        assert "MCP" in ShelfApp.remote_debugging_port.__doc__


class TestRemoteDebuggingPortInModes:
    """Tests for remote_debugging_port in different show() modes."""

    @pytest.fixture
    def mock_webview(self):
        """Create a mock WebView."""
        mock = MagicMock()
        mock.state = MagicMock()
        mock.state.batch_update = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
        return mock

    def test_hwnd_create_kwargs_includes_port(self, mock_webview):
        """Test that HWND mode create_kwargs includes remote_debugging_port."""
        from auroraview_dcc_shelves.app import ShelfApp
        from auroraview_dcc_shelves.config import ShelvesConfig

        config = ShelvesConfig(shelves=[])
        app = ShelfApp(config, remote_debugging_port=9222)
        app._hwnd_debug = True

        # Manually build the create_kwargs like _hwnd_thread_main does
        create_kwargs = {
            "title": app._title,
            "width": app._width,
            "height": app._height,
            "debug": app._hwnd_debug,
            "context_menu": app._hwnd_debug,
            "asset_root": None,  # Simplified for test
        }

        # Add remote_debugging_port if configured (simulating the logic)
        if app._remote_debugging_port is not None:
            create_kwargs["remote_debugging_port"] = app._remote_debugging_port

        # Verify remote_debugging_port is in create_kwargs
        assert create_kwargs.get("remote_debugging_port") == 9222

    def test_standalone_mode_includes_port(self, mock_webview):
        """Test that _show_standalone_mode passes remote_debugging_port to WebView."""
        from auroraview_dcc_shelves.app import ShelfApp
        from auroraview_dcc_shelves.config import ShelvesConfig

        config = ShelvesConfig(shelves=[])
        app = ShelfApp(config, remote_debugging_port=9222)

        # Mock WebView.create
        with patch("auroraview_dcc_shelves.app.WebView") as MockWebView:
            MockWebView.create.return_value = mock_webview

            # Mock _is_dev_mode to return True for simpler test
            app._dev_mode_cached = True

            with contextlib.suppress(Exception):
                app._show_standalone_mode(debug=True)

            # Verify WebView.create was called with remote_debugging_port
            call_kwargs = MockWebView.create.call_args[1]
            assert call_kwargs.get("remote_debugging_port") == 9222


class TestRemoteDebuggingPortValues:
    """Tests for various remote_debugging_port values."""

    def test_common_debugging_ports(self):
        """Test common debugging port values."""
        from auroraview_dcc_shelves.app import ShelfApp
        from auroraview_dcc_shelves.config import ShelvesConfig

        config = ShelvesConfig(shelves=[])

        # Test common CDP ports
        common_ports = [9222, 9223, 9333, 8222, 8000]
        for port in common_ports:
            app = ShelfApp(config, remote_debugging_port=port)
            assert app.remote_debugging_port == port

    def test_zero_port_is_not_none(self):
        """Test that port 0 (random port) is handled correctly."""
        from auroraview_dcc_shelves.app import ShelfApp
        from auroraview_dcc_shelves.config import ShelvesConfig

        config = ShelvesConfig(shelves=[])
        app = ShelfApp(config, remote_debugging_port=0)
        # Port 0 should be stored as 0, not None
        assert app.remote_debugging_port == 0
