"""Tests for window settings persistence."""

from __future__ import annotations

import json

from pyfakefs.fake_filesystem import FakeFilesystem

from auroraview_dcc_shelves.settings import (
    WindowSettings,
    WindowSettingsManager,
)


class TestWindowSettings:
    """Tests for WindowSettings data class."""

    def test_default_values(self):
        """Test default window settings."""
        settings = WindowSettings()
        assert settings.width == 800
        assert settings.height == 600
        assert settings.x == -1
        assert settings.y == -1

    def test_custom_values(self):
        """Test custom window settings."""
        settings = WindowSettings(width=1024, height=768, x=100, y=200)
        assert settings.width == 1024
        assert settings.height == 768
        assert settings.x == 100
        assert settings.y == 200

    def test_to_dict(self):
        """Test conversion to dictionary."""
        settings = WindowSettings(width=1024, height=768, x=50, y=100)
        data = settings.to_dict()
        assert data == {"width": 1024, "height": 768, "x": 50, "y": 100}

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {"width": 1280, "height": 720, "x": 0, "y": 0}
        settings = WindowSettings.from_dict(data)
        assert settings.width == 1280
        assert settings.height == 720
        assert settings.x == 0
        assert settings.y == 0

    def test_from_dict_with_missing_keys(self):
        """Test creation from incomplete dictionary."""
        data = {"width": 1024}
        settings = WindowSettings.from_dict(data)
        assert settings.width == 1024
        assert settings.height == 600  # default
        assert settings.x == -1  # default
        assert settings.y == -1  # default

    def test_from_dict_empty(self):
        """Test creation from empty dictionary."""
        settings = WindowSettings.from_dict({})
        assert settings.width == 800
        assert settings.height == 600


class TestWindowSettingsManager:
    """Tests for WindowSettingsManager class."""

    def test_init_default_app(self, fs: FakeFilesystem):
        """Test initialization with default app name."""
        manager = WindowSettingsManager()
        assert "standalone" in str(manager._settings_file)

    def test_init_custom_app(self, fs: FakeFilesystem):
        """Test initialization with custom app name."""
        manager = WindowSettingsManager("maya")
        assert "maya" in str(manager._settings_file)

    def test_init_case_insensitive(self, fs: FakeFilesystem):
        """Test app name is normalized to lowercase."""
        manager = WindowSettingsManager("MAYA")
        assert "maya" in str(manager._settings_file)

    def test_load_no_file(self, fs: FakeFilesystem):
        """Test loading when no settings file exists."""
        manager = WindowSettingsManager("maya")
        settings = manager.load()
        # Should return defaults
        assert settings.width == 800
        assert settings.height == 600

    def test_save_and_load(self, fs: FakeFilesystem):
        """Test saving and loading settings."""
        manager = WindowSettingsManager("maya")

        # Save custom settings
        settings = WindowSettings(width=1024, height=768, x=100, y=200)
        manager.save(settings)

        # Create new manager and load
        manager2 = WindowSettingsManager("maya")
        loaded = manager2.load()

        assert loaded.width == 1024
        assert loaded.height == 768
        assert loaded.x == 100
        assert loaded.y == 200

    def test_save_creates_directory(self, fs: FakeFilesystem):
        """Test that save creates settings directory if needed."""
        manager = WindowSettingsManager("nuke")
        settings = WindowSettings(width=1920, height=1080)

        # Directory shouldn't exist yet
        assert not manager._settings_dir.exists()

        manager.save(settings)

        # Now it should exist
        assert manager._settings_dir.exists()
        assert manager._settings_file.exists()

    def test_load_caching(self, fs: FakeFilesystem):
        """Test that settings are cached after first load."""
        manager = WindowSettingsManager("maya")

        # First load
        settings1 = manager.load()

        # Modify the file directly
        manager._settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(manager._settings_file, "w") as f:
            json.dump({"width": 9999, "height": 9999}, f)

        # Second load should return cached value
        settings2 = manager.load()
        assert settings1.width == settings2.width  # Still default, not 9999

    def test_per_app_settings(self, fs: FakeFilesystem):
        """Test that different apps have separate settings."""
        maya_manager = WindowSettingsManager("maya")
        nuke_manager = WindowSettingsManager("nuke")

        # Save different settings
        maya_manager.save(WindowSettings(width=800, height=600))
        nuke_manager.save(WindowSettings(width=1920, height=1080))

        # Load and verify
        maya_settings = WindowSettingsManager("maya").load()
        nuke_settings = WindowSettingsManager("nuke").load()

        assert maya_settings.width == 800
        assert nuke_settings.width == 1920
