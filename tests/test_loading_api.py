"""Tests for loading state and warmup API integration in ShelfApp."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from auroraview_dcc_shelves.config import ShelvesConfig
from auroraview_dcc_shelves import (
    start_warmup,
    warmup_sync,
    is_warmup_complete,
    get_warmup_progress,
    get_warmup_stage,
    get_warmup_status,
)


class TestLoadingStateAPI:
    """Tests for ShelfApp loading state properties and methods."""

    @pytest.fixture
    def mock_config(self):
        """Create a minimal mock config."""
        return ShelvesConfig(shelves=[])

    @pytest.fixture
    def shelf_app(self, mock_config):
        """Create a ShelfApp instance for testing."""
        from auroraview_dcc_shelves.ui import ShelfApp

        return ShelfApp(config=mock_config, title="Test", width=400, height=600)

    def test_is_loading_default(self, shelf_app):
        """Test is_loading default value."""
        assert shelf_app.is_loading is False

    def test_load_progress_default(self, shelf_app):
        """Test load_progress default value."""
        assert shelf_app.load_progress == 0

    def test_current_url_default(self, shelf_app):
        """Test current_url default value."""
        assert shelf_app.current_url == ""

    def test_stop_without_webview(self, shelf_app, caplog):
        """Test stop() when WebView is not initialized."""
        shelf_app.stop()
        assert "Cannot stop: WebView not initialized" in caplog.text

    def test_on_navigation_started_callback(self, shelf_app):
        """Test registering navigation started callback."""
        callback = MagicMock()
        shelf_app.on_navigation_started(callback)
        assert callback in shelf_app._navigation_callbacks["navigation_started"]

    def test_on_navigation_completed_callback(self, shelf_app):
        """Test registering navigation completed callback."""
        callback = MagicMock()
        shelf_app.on_navigation_completed(callback)
        assert callback in shelf_app._navigation_callbacks["navigation_completed"]

    def test_on_navigation_failed_callback(self, shelf_app):
        """Test registering navigation failed callback."""
        callback = MagicMock()
        shelf_app.on_navigation_failed(callback)
        assert callback in shelf_app._navigation_callbacks["navigation_failed"]

    def test_on_load_progress_callback(self, shelf_app):
        """Test registering load progress callback."""
        callback = MagicMock()
        shelf_app.on_load_progress(callback)
        assert callback in shelf_app._navigation_callbacks["load_progress"]

    def test_emit_navigation_event(self, shelf_app):
        """Test emitting navigation events to callbacks."""
        callback = MagicMock()
        shelf_app.on_navigation_started(callback)

        shelf_app._emit_navigation_event("navigation_started", "https://example.com")

        callback.assert_called_once_with("https://example.com")

    def test_emit_navigation_event_with_error(self, shelf_app, caplog):
        """Test that callback errors are logged."""

        def bad_callback(url):
            raise ValueError("Test error")

        shelf_app.on_navigation_started(bad_callback)
        shelf_app._emit_navigation_event("navigation_started", "https://example.com")

        assert "Navigation callback error" in caplog.text


class TestEvalJsAsync:
    """Tests for eval_js_async method."""

    @pytest.fixture
    def mock_config(self):
        """Create a minimal mock config."""
        return ShelvesConfig(shelves=[])

    @pytest.fixture
    def shelf_app(self, mock_config):
        """Create a ShelfApp instance for testing."""
        from auroraview_dcc_shelves.ui import ShelfApp

        return ShelfApp(config=mock_config, title="Test", width=400, height=600)

    def test_eval_js_async_without_webview(self, shelf_app):
        """Test eval_js_async when WebView is not initialized."""
        callback = MagicMock()
        shelf_app.eval_js_async("console.log('test')", callback)

        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] is None  # result
        assert isinstance(args[1], RuntimeError)  # error

    def test_eval_js_async_with_webview_supporting_async(self, shelf_app):
        """Test eval_js_async with webview that supports async."""
        mock_webview = MagicMock()
        mock_webview.eval_js_async = MagicMock()
        shelf_app._webview = mock_webview

        callback = MagicMock()
        shelf_app.eval_js_async("document.title", callback, timeout_ms=3000)

        mock_webview.eval_js_async.assert_called_once_with("document.title", callback, 3000)

    def test_eval_js_async_fallback_to_sync(self, shelf_app):
        """Test eval_js_async fallback to sync eval_js."""
        mock_webview = MagicMock()
        del mock_webview.eval_js_async  # Remove async method
        mock_webview.eval_js = MagicMock(return_value="Test Title")
        shelf_app._webview = mock_webview

        callback = MagicMock()
        shelf_app.eval_js_async("document.title", callback)

        callback.assert_called_once_with("Test Title", None)

    def test_eval_js_async_fallback_with_error(self, shelf_app):
        """Test eval_js_async fallback when sync eval_js raises."""
        mock_webview = MagicMock()
        del mock_webview.eval_js_async
        mock_webview.eval_js = MagicMock(side_effect=ValueError("JS Error"))
        shelf_app._webview = mock_webview

        callback = MagicMock()
        shelf_app.eval_js_async("bad_code()", callback)

        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] is None  # result
        assert isinstance(args[1], ValueError)  # error


class TestQtSignalConnection:
    """Tests for Qt signal connection methods."""

    @pytest.fixture
    def mock_config(self):
        """Create a minimal mock config."""
        return ShelvesConfig(shelves=[])

    @pytest.fixture
    def shelf_app(self, mock_config):
        """Create a ShelfApp instance for testing."""
        from auroraview_dcc_shelves.ui import ShelfApp

        return ShelfApp(config=mock_config, title="Test", width=400, height=600)

    def test_on_qt_load_started(self, shelf_app):
        """Test Qt loadStarted signal handler."""
        callback = MagicMock()
        shelf_app.on_navigation_started(callback)

        shelf_app._on_qt_load_started()

        assert shelf_app._is_loading is True
        assert shelf_app._load_progress == 0
        callback.assert_called_once()

    def test_on_qt_load_finished_success(self, shelf_app):
        """Test Qt loadFinished signal handler with success."""
        callback = MagicMock()
        shelf_app.on_navigation_completed(callback)

        shelf_app._on_qt_load_finished(True)

        assert shelf_app._is_loading is False
        assert shelf_app._load_progress == 100
        callback.assert_called_once()

    def test_on_qt_load_finished_failure(self, shelf_app):
        """Test Qt loadFinished signal handler with failure."""
        callback = MagicMock()
        shelf_app.on_navigation_failed(callback)

        shelf_app._on_qt_load_finished(False)

        assert shelf_app._is_loading is False
        assert shelf_app._load_progress == 0
        callback.assert_called_once()

    def test_on_qt_load_progress(self, shelf_app):
        """Test Qt loadProgress signal handler."""
        callback = MagicMock()
        shelf_app.on_load_progress(callback)

        shelf_app._on_qt_load_progress(50)

        assert shelf_app._load_progress == 50
        callback.assert_called_once_with(50)

    def test_on_qt_url_changed(self, shelf_app):
        """Test Qt urlChanged signal handler."""
        shelf_app._on_qt_url_changed("https://example.com")
        assert shelf_app._current_url == "https://example.com"

    def test_notify_frontend_loading_state(self, shelf_app):
        """Test frontend notification for loading state."""
        mock_webview = MagicMock()
        shelf_app._webview = mock_webview

        shelf_app._notify_frontend_loading_state(True, 50)

        mock_webview.emit.assert_called_once_with(
            "loading_state",
            {
                "isLoading": True,
                "progress": 50,
            },
        )

    def test_notify_frontend_loading_state_no_webview(self, shelf_app):
        """Test frontend notification when webview is None."""
        # Should not raise
        shelf_app._notify_frontend_loading_state(True, 50)


class TestWarmupAPI:
    """Tests for WebView2 warmup API."""

    def test_start_warmup_returns_bool(self):
        """Test start_warmup returns a boolean."""
        result = start_warmup()
        assert isinstance(result, bool)

    def test_warmup_sync_returns_bool(self):
        """Test warmup_sync returns a boolean."""
        result = warmup_sync(timeout_ms=100)
        assert isinstance(result, bool)

    def test_is_warmup_complete_returns_bool(self):
        """Test is_warmup_complete returns a boolean."""
        result = is_warmup_complete()
        assert isinstance(result, bool)

    def test_get_warmup_progress_returns_int(self):
        """Test get_warmup_progress returns an integer."""
        result = get_warmup_progress()
        assert isinstance(result, int)
        assert 0 <= result <= 100

    def test_get_warmup_stage_returns_str(self):
        """Test get_warmup_stage returns a string."""
        result = get_warmup_stage()
        assert isinstance(result, str)

    def test_get_warmup_status_returns_dict(self):
        """Test get_warmup_status returns a dictionary with expected keys."""
        result = get_warmup_status()
        assert isinstance(result, dict)
        # Check expected keys
        expected_keys = ["initiated", "complete", "progress", "stage", "duration_ms", "error", "user_data_folder"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_get_warmup_status_types(self):
        """Test get_warmup_status returns correct types."""
        result = get_warmup_status()
        assert isinstance(result["initiated"], bool)
        assert isinstance(result["complete"], bool)
        assert isinstance(result["progress"], int)
        assert isinstance(result["stage"], str)


class TestShelfAppWarmupMethods:
    """Tests for ShelfApp warmup static methods."""

    @pytest.fixture
    def mock_config(self):
        """Create a minimal mock config."""
        return ShelvesConfig(shelves=[])

    @pytest.fixture
    def shelf_app(self, mock_config):
        """Create a ShelfApp instance for testing."""
        from auroraview_dcc_shelves.ui import ShelfApp

        return ShelfApp(config=mock_config, title="Test", width=400, height=600)

    def test_static_start_warmup(self):
        """Test ShelfApp.start_warmup is a static method."""
        from auroraview_dcc_shelves.ui import ShelfApp

        # Should be callable without instance
        result = ShelfApp.start_warmup()
        assert isinstance(result, bool)

    def test_static_is_warmup_complete(self):
        """Test ShelfApp.is_warmup_complete is a static method."""
        from auroraview_dcc_shelves.ui import ShelfApp

        result = ShelfApp.is_warmup_complete()
        assert isinstance(result, bool)

    def test_static_get_warmup_status(self):
        """Test ShelfApp.get_warmup_status is a static method."""
        from auroraview_dcc_shelves.ui import ShelfApp

        result = ShelfApp.get_warmup_status()
        assert isinstance(result, dict)

    def test_on_warmup_progress_callback(self, shelf_app):
        """Test registering warmup progress callback."""
        callback = MagicMock()
        shelf_app.on_warmup_progress(callback)
        assert callback in shelf_app._navigation_callbacks["warmup_progress"]


class TestZoomAPI:
    """Tests for ShelfApp zoom API."""

    @pytest.fixture
    def mock_config(self):
        """Create a minimal mock config."""
        return ShelvesConfig(shelves=[])

    @pytest.fixture
    def shelf_app(self, mock_config):
        """Create a ShelfApp instance for testing."""
        from auroraview_dcc_shelves.ui import ShelfApp

        return ShelfApp(config=mock_config, title="Test", width=400, height=600)

    def test_zoom_default_value(self, shelf_app):
        """Test default zoom level is 1.0."""
        assert shelf_app.get_zoom() == 1.0

    def test_zoom_initial_attributes(self, shelf_app):
        """Test zoom-related attributes are initialized."""
        assert hasattr(shelf_app, "_current_zoom")
        assert hasattr(shelf_app, "_auto_zoom_enabled")
        assert shelf_app._current_zoom == 1.0
        assert shelf_app._auto_zoom_enabled is True

    def test_set_zoom_without_webview(self, shelf_app, caplog):
        """Test set_zoom returns False when WebView not initialized."""
        result = shelf_app.set_zoom(1.5)
        assert result is False
        assert "Cannot set zoom: WebView not initialized" in caplog.text

    def test_zoom_in_without_webview(self, shelf_app):
        """Test zoom_in returns False when WebView not initialized."""
        result = shelf_app.zoom_in()
        assert result is False

    def test_zoom_out_without_webview(self, shelf_app):
        """Test zoom_out returns False when WebView not initialized."""
        result = shelf_app.zoom_out()
        assert result is False

    def test_reset_zoom_without_webview(self, shelf_app):
        """Test reset_zoom returns False when WebView not initialized."""
        result = shelf_app.reset_zoom()
        assert result is False

    def test_set_zoom_with_mock_webview(self, shelf_app):
        """Test set_zoom with a mock WebView supporting set_zoom."""
        mock_webview = MagicMock()
        mock_webview.set_zoom = MagicMock()
        shelf_app._webview = mock_webview

        result = shelf_app.set_zoom(1.25)
        assert result is True
        assert shelf_app.get_zoom() == 1.25
        mock_webview.set_zoom.assert_called_once_with(1.25)

    def test_set_zoom_with_js_fallback(self, shelf_app):
        """Test set_zoom falls back to CSS zoom when set_zoom not available."""
        mock_webview = MagicMock(spec=["eval_js"])
        mock_webview.eval_js = MagicMock()
        shelf_app._webview = mock_webview

        result = shelf_app.set_zoom(1.5)
        assert result is True
        assert shelf_app.get_zoom() == 1.5
        mock_webview.eval_js.assert_called_once()
        # Check that CSS zoom was set
        call_arg = mock_webview.eval_js.call_args[0][0]
        assert "1.5" in call_arg

    def test_zoom_in_increases_zoom(self, shelf_app):
        """Test zoom_in increases zoom level by step."""
        mock_webview = MagicMock()
        mock_webview.set_zoom = MagicMock()
        shelf_app._webview = mock_webview
        shelf_app._current_zoom = 1.0

        shelf_app.zoom_in(0.1)
        assert shelf_app.get_zoom() == 1.1

    def test_zoom_out_decreases_zoom(self, shelf_app):
        """Test zoom_out decreases zoom level by step."""
        mock_webview = MagicMock()
        mock_webview.set_zoom = MagicMock()
        shelf_app._webview = mock_webview
        shelf_app._current_zoom = 1.0

        shelf_app.zoom_out(0.1)
        assert shelf_app.get_zoom() == 0.9

    def test_zoom_max_limit(self, shelf_app):
        """Test zoom cannot exceed maximum limit (3.0)."""
        mock_webview = MagicMock()
        mock_webview.set_zoom = MagicMock()
        shelf_app._webview = mock_webview
        shelf_app._current_zoom = 2.9

        shelf_app.zoom_in(0.2)
        assert shelf_app.get_zoom() == 3.0

    def test_zoom_min_limit(self, shelf_app):
        """Test zoom cannot go below minimum limit (0.5)."""
        mock_webview = MagicMock()
        mock_webview.set_zoom = MagicMock()
        shelf_app._webview = mock_webview
        shelf_app._current_zoom = 0.6

        shelf_app.zoom_out(0.2)
        assert shelf_app.get_zoom() == 0.5

    def test_reset_zoom_sets_to_100(self, shelf_app):
        """Test reset_zoom sets zoom to 1.0."""
        mock_webview = MagicMock()
        mock_webview.set_zoom = MagicMock()
        shelf_app._webview = mock_webview
        shelf_app._current_zoom = 1.5

        result = shelf_app.reset_zoom()
        assert result is True
        assert shelf_app.get_zoom() == 1.0

    def test_calculate_optimal_zoom_4k(self, shelf_app):
        """Test optimal zoom calculation for 4K displays."""
        zoom = shelf_app._calculate_optimal_zoom(3840, 2160, 96, 1.0)
        assert 1.2 <= zoom <= 1.5  # Should be around 125%

    def test_calculate_optimal_zoom_2k(self, shelf_app):
        """Test optimal zoom calculation for 2K displays."""
        zoom = shelf_app._calculate_optimal_zoom(2560, 1440, 96, 1.0)
        assert 1.0 <= zoom <= 1.2  # Should be around 110%

    def test_calculate_optimal_zoom_fullhd(self, shelf_app):
        """Test optimal zoom calculation for Full HD displays."""
        zoom = shelf_app._calculate_optimal_zoom(1920, 1080, 96, 1.0)
        assert 0.95 <= zoom <= 1.05  # Should be around 100%

    def test_calculate_optimal_zoom_laptop(self, shelf_app):
        """Test optimal zoom calculation for laptop displays."""
        zoom = shelf_app._calculate_optimal_zoom(1366, 768, 96, 1.0)
        assert 0.9 <= zoom <= 1.0  # Should be around 95%

    def test_calculate_optimal_zoom_hidpi(self, shelf_app):
        """Test optimal zoom calculation for HiDPI displays."""
        zoom = shelf_app._calculate_optimal_zoom(3840, 2160, 96, 2.0)
        # HiDPI should compensate for OS scaling
        assert zoom <= 1.3
