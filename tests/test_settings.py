"""Tests for DCC state persistence.

This module tests the DCCState and DCCStateManager classes which handle
DCC-specific state persistence. Window size is no longer persisted as
it's fixed by design.
"""

from __future__ import annotations

import json

from pyfakefs.fake_filesystem import FakeFilesystem

from auroraview_dcc_shelves.settings import (
    DCCState,
    DCCStateManager,
    WindowSettings,
    WindowSettingsManager,
)


class TestWindowSettings:
    """Tests for WindowSettings data class (legacy, returns defaults only)."""

    def test_default_values(self):
        """Test default window settings (0 means use default)."""
        settings = WindowSettings()
        # New implementation uses 0 to indicate "use default"
        assert settings.width == 0
        assert settings.height == 0
        assert settings.x == -1
        assert settings.y == -1

    def test_custom_values(self):
        """Test custom window settings."""
        settings = WindowSettings(width=1024, height=768, x=100, y=200)
        assert settings.width == 1024
        assert settings.height == 768
        assert settings.x == 100
        assert settings.y == 200


class TestWindowSettingsManager:
    """Tests for WindowSettingsManager class (legacy, no-op for size)."""

    def test_init_default_app(self, fs: FakeFilesystem):
        """Test initialization with default app name."""
        manager = WindowSettingsManager()
        # Uses DCCStateManager internally
        assert manager._dcc_state.dcc_name == "standalone"

    def test_init_custom_app(self, fs: FakeFilesystem):
        """Test initialization with custom app name."""
        manager = WindowSettingsManager("maya")
        assert manager._dcc_state.dcc_name == "maya"

    def test_init_case_insensitive(self, fs: FakeFilesystem):
        """Test app name is normalized to lowercase."""
        manager = WindowSettingsManager("MAYA")
        assert manager._dcc_state.dcc_name == "maya"

    def test_load_returns_defaults(self, fs: FakeFilesystem):
        """Test loading returns default settings (size is fixed)."""
        manager = WindowSettingsManager("maya")
        settings = manager.load()
        # Returns defaults since size is no longer persisted
        assert settings.width == 0
        assert settings.height == 0

    def test_save_is_noop(self, fs: FakeFilesystem):
        """Test that save is a no-op (size is fixed)."""
        manager = WindowSettingsManager("maya")
        # Should not raise, but does nothing
        manager.save(1024, 768)


class TestDCCState:
    """Tests for DCCState data class."""

    def test_default_values(self):
        """Test default DCC state values."""
        state = DCCState()
        assert state.collapsed_shelves == []
        assert state.last_active_shelf == ""
        assert state.bottom_panel_tab == "info"
        assert state.bottom_panel_expanded is True
        assert state.custom_data == {}

    def test_custom_values(self):
        """Test custom DCC state values."""
        state = DCCState(
            collapsed_shelves=["shelf1", "shelf2"],
            last_active_shelf="shelf1",
            bottom_panel_tab="details",
            bottom_panel_expanded=False,
            custom_data={"key": "value"},
        )
        assert state.collapsed_shelves == ["shelf1", "shelf2"]
        assert state.last_active_shelf == "shelf1"
        assert state.bottom_panel_tab == "details"
        assert state.bottom_panel_expanded is False
        assert state.custom_data == {"key": "value"}

    def test_to_dict(self):
        """Test conversion to dictionary."""
        state = DCCState(
            collapsed_shelves=["shelf1"],
            last_active_shelf="shelf1",
            bottom_panel_tab="details",
            bottom_panel_expanded=False,
            custom_data={"key": "value"},
        )
        data = state.to_dict()
        assert data == {
            "collapsed_shelves": ["shelf1"],
            "last_active_shelf": "shelf1",
            "bottom_panel_tab": "details",
            "bottom_panel_expanded": False,
            "custom_data": {"key": "value"},
        }

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "collapsed_shelves": ["shelf1", "shelf2"],
            "last_active_shelf": "shelf2",
            "bottom_panel_tab": "info",
            "bottom_panel_expanded": True,
            "custom_data": {"foo": "bar"},
        }
        state = DCCState.from_dict(data)
        assert state.collapsed_shelves == ["shelf1", "shelf2"]
        assert state.last_active_shelf == "shelf2"
        assert state.bottom_panel_tab == "info"
        assert state.bottom_panel_expanded is True
        assert state.custom_data == {"foo": "bar"}

    def test_from_dict_with_missing_keys(self):
        """Test creation from incomplete dictionary."""
        data = {"collapsed_shelves": ["shelf1"]}
        state = DCCState.from_dict(data)
        assert state.collapsed_shelves == ["shelf1"]
        assert state.last_active_shelf == ""  # default
        assert state.bottom_panel_tab == "info"  # default
        assert state.bottom_panel_expanded is True  # default
        assert state.custom_data == {}  # default

    def test_from_dict_empty(self):
        """Test creation from empty dictionary."""
        state = DCCState.from_dict({})
        assert state.collapsed_shelves == []
        assert state.last_active_shelf == ""


class TestDCCStateManager:
    """Tests for DCCStateManager class."""

    def test_init_default_app(self, fs: FakeFilesystem):
        """Test initialization with default app name."""
        manager = DCCStateManager()
        assert manager.dcc_name == "standalone"

    def test_init_custom_app(self, fs: FakeFilesystem):
        """Test initialization with custom app name."""
        manager = DCCStateManager("maya")
        assert manager.dcc_name == "maya"

    def test_init_case_insensitive(self, fs: FakeFilesystem):
        """Test app name is normalized to lowercase."""
        manager = DCCStateManager("MAYA")
        assert manager.dcc_name == "maya"

    def test_load_no_file(self, fs: FakeFilesystem):
        """Test loading when no state file exists."""
        manager = DCCStateManager("maya")
        state = manager.load()
        # Should return defaults
        assert state.collapsed_shelves == []
        assert state.last_active_shelf == ""

    def test_save_and_load(self, fs: FakeFilesystem):
        """Test saving and loading state."""
        manager = DCCStateManager("maya")

        # Save custom state
        state = DCCState(
            collapsed_shelves=["shelf1"],
            last_active_shelf="shelf1",
            bottom_panel_tab="details",
        )
        manager.save(state)

        # Create new manager and load
        manager2 = DCCStateManager("maya")
        loaded = manager2.load()

        assert loaded.collapsed_shelves == ["shelf1"]
        assert loaded.last_active_shelf == "shelf1"
        assert loaded.bottom_panel_tab == "details"

    def test_save_creates_directory(self, fs: FakeFilesystem):
        """Test that save creates settings directory if needed."""
        manager = DCCStateManager("nuke")
        state = DCCState(collapsed_shelves=["shelf1"])

        # Directory shouldn't exist yet
        assert not manager._settings_dir.exists()

        manager.save(state)

        # Now it should exist
        assert manager._settings_dir.exists()
        assert manager._state_file.exists()

    def test_load_caching(self, fs: FakeFilesystem):
        """Test that state is cached after first load."""
        manager = DCCStateManager("maya")

        # First load
        state1 = manager.load()

        # Modify the file directly
        manager._settings_dir.mkdir(parents=True, exist_ok=True)
        with open(manager._state_file, "w") as f:
            json.dump({"collapsed_shelves": ["modified"]}, f)

        # Second load should return cached value
        state2 = manager.load()
        assert state1.collapsed_shelves == state2.collapsed_shelves  # Still default

    def test_per_app_state(self, fs: FakeFilesystem):
        """Test that different apps have separate state."""
        maya_manager = DCCStateManager("maya")
        nuke_manager = DCCStateManager("nuke")

        # Save different state
        maya_manager.save(DCCState(last_active_shelf="maya_shelf"))
        nuke_manager.save(DCCState(last_active_shelf="nuke_shelf"))

        # Load and verify
        maya_state = DCCStateManager("maya").load()
        nuke_state = DCCStateManager("nuke").load()

        assert maya_state.last_active_shelf == "maya_shelf"
        assert nuke_state.last_active_shelf == "nuke_shelf"

    def test_update_method(self, fs: FakeFilesystem):
        """Test the update method for partial updates."""
        manager = DCCStateManager("maya")

        # Update specific fields
        manager.update(last_active_shelf="shelf1", bottom_panel_expanded=False)

        # Load and verify
        state = DCCStateManager("maya").load()
        assert state.last_active_shelf == "shelf1"
        assert state.bottom_panel_expanded is False

    def test_custom_data_methods(self, fs: FakeFilesystem):
        """Test get_custom and set_custom methods."""
        manager = DCCStateManager("maya")

        # Set custom data
        manager.set_custom("my_key", "my_value")

        # Get custom data
        value = manager.get_custom("my_key")
        assert value == "my_value"

        # Get with default
        default_value = manager.get_custom("nonexistent", "default")
        assert default_value == "default"
