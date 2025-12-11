"""Tests for DCC adapters and hook system."""

from __future__ import annotations

from auroraview_dcc_shelves.apps.base import (
    GenericAdapter,
    QtConfig,
    _detect_qt6,
    get_adapter,
)


class TestDetectQt6:
    """Tests for _detect_qt6 function."""

    def test_detect_qt6_returns_bool(self):
        """Test that _detect_qt6 returns a boolean."""
        result = _detect_qt6()
        assert isinstance(result, bool)

    def test_detect_qt6_consistent(self):
        """Test that _detect_qt6 returns consistent results."""
        result1 = _detect_qt6()
        result2 = _detect_qt6()
        assert result1 == result2


class TestQtConfig:
    """Tests for QtConfig dataclass."""

    def test_default_values(self):
        """Test default QtConfig values."""
        config = QtConfig()
        assert config.init_delay_ms == 10
        assert config.timer_interval_ms == 16
        assert config.geometry_fix_delays == [100, 500, 1000, 2000]
        assert config.force_opaque_window is False
        assert config.disable_translucent is False
        assert config.is_qt6 is False

    def test_custom_values(self):
        """Test QtConfig with custom values."""
        config = QtConfig(
            init_delay_ms=100,
            timer_interval_ms=50,
            geometry_fix_delays=[100, 300, 600],
            force_opaque_window=True,
            disable_translucent=True,
            is_qt6=True,
        )
        assert config.init_delay_ms == 100
        assert config.timer_interval_ms == 50
        assert config.geometry_fix_delays == [100, 300, 600]
        assert config.force_opaque_window is True
        assert config.disable_translucent is True
        assert config.is_qt6 is True


class TestGenericAdapter:
    """Tests for GenericAdapter."""

    def test_name(self):
        """Test adapter name."""
        adapter = GenericAdapter()
        assert adapter.name == "Generic"

    def test_timer_interval(self):
        """Test default timer interval."""
        adapter = GenericAdapter()
        assert adapter.timer_interval_ms == 16

    def test_qt_config_lazy_init(self):
        """Test that qt_config is lazily initialized."""
        adapter = GenericAdapter()
        assert adapter._qt_config is None
        _ = adapter.qt_config
        assert adapter._qt_config is not None

    def test_get_init_delay_ms(self):
        """Test get_init_delay_ms hook."""
        adapter = GenericAdapter()
        assert adapter.get_init_delay_ms() == 10

    def test_get_geometry_fix_delays(self):
        """Test get_geometry_fix_delays hook."""
        adapter = GenericAdapter()
        delays = adapter.get_geometry_fix_delays()
        assert delays == [100, 500, 1000, 2000]


class TestMayaAdapter:
    """Tests for MayaAdapter."""

    def test_import(self):
        """Test MayaAdapter can be imported."""
        from auroraview_dcc_shelves.apps.maya import MayaAdapter

        adapter = MayaAdapter()
        assert adapter.name == "Maya"

    def test_qt_config(self):
        """Test Maya Qt configuration (dynamically detected)."""
        from auroraview_dcc_shelves.apps.maya import MayaAdapter

        adapter = MayaAdapter()
        config = adapter.qt_config
        # Timer interval is always 16ms for Maya
        assert config.timer_interval_ms == 16
        # Init delay depends on Qt version (10ms for Qt5, 50ms for Qt6)
        assert config.init_delay_ms in (10, 50)
        # Qt6 optimizations should match is_qt6 flag
        if config.is_qt6:
            assert config.force_opaque_window is True
            assert config.disable_translucent is True
        else:
            assert config.force_opaque_window is False
            assert config.disable_translucent is False


class TestNukeAdapter:
    """Tests for NukeAdapter."""

    def test_import(self):
        """Test NukeAdapter can be imported."""
        from auroraview_dcc_shelves.apps.nuke import NukeAdapter

        adapter = NukeAdapter()
        assert adapter.name == "Nuke"

    def test_qt_config(self):
        """Test Nuke Qt configuration (dynamically detected)."""
        from auroraview_dcc_shelves.apps.nuke import NukeAdapter

        adapter = NukeAdapter()
        config = adapter.qt_config
        # Timer interval is always 32ms for Nuke
        assert config.timer_interval_ms == 32
        # Nuke has extended geometry fix delays
        assert len(config.geometry_fix_delays) == 5
        # Qt6 optimizations should match is_qt6 flag
        if config.is_qt6:
            assert config.force_opaque_window is True
        else:
            assert config.force_opaque_window is False


class TestHoudiniAdapter:
    """Tests for HoudiniAdapter."""

    def test_import(self):
        """Test HoudiniAdapter can be imported."""
        from auroraview_dcc_shelves.apps.houdini import HoudiniAdapter

        adapter = HoudiniAdapter()
        assert adapter.name == "Houdini"

    def test_qt_config(self):
        """Test Houdini Qt configuration (dynamically detected)."""
        from auroraview_dcc_shelves.apps.houdini import HoudiniAdapter

        adapter = HoudiniAdapter()
        config = adapter.qt_config
        # Houdini always uses longer delays due to heavy main thread
        assert config.init_delay_ms == 100
        assert config.timer_interval_ms == 50
        # Qt6 optimizations should match is_qt6 flag
        if config.is_qt6:
            assert config.force_opaque_window is True
            assert config.disable_translucent is True
        else:
            assert config.force_opaque_window is False
            assert config.disable_translucent is False


class TestAdapterRegistry:
    """Tests for adapter registry."""

    def test_get_maya_adapter(self):
        """Test getting Maya adapter."""
        adapter = get_adapter("maya")
        assert adapter.name == "Maya"

    def test_get_nuke_adapter(self):
        """Test getting Nuke adapter."""
        adapter = get_adapter("nuke")
        assert adapter.name == "Nuke"

    def test_get_houdini_adapter(self):
        """Test getting Houdini adapter."""
        adapter = get_adapter("houdini")
        assert adapter.name == "Houdini"

    def test_get_unknown_adapter(self):
        """Test getting unknown adapter returns GenericAdapter."""
        adapter = get_adapter("unknown_dcc")
        assert adapter.name == "Generic"


class TestDockableSupport:
    """Tests for dockable panel support in adapters."""

    def test_generic_adapter_no_dockable(self):
        """Test that GenericAdapter does not support dockable."""
        adapter = GenericAdapter()
        assert adapter.supports_dockable() is False

    def test_maya_adapter_supports_dockable(self):
        """Test that MayaAdapter supports dockable."""
        from auroraview_dcc_shelves.apps.maya import MayaAdapter

        adapter = MayaAdapter()
        assert adapter.supports_dockable() is True

    def test_nuke_adapter_supports_dockable(self):
        """Test that NukeAdapter supports dockable."""
        from auroraview_dcc_shelves.apps.nuke import NukeAdapter

        adapter = NukeAdapter()
        assert adapter.supports_dockable() is True

    def test_houdini_adapter_supports_dockable(self):
        """Test that HoudiniAdapter supports dockable."""
        from auroraview_dcc_shelves.apps.houdini import HoudiniAdapter

        adapter = HoudiniAdapter()
        assert adapter.supports_dockable() is True

    def test_base_adapter_dockable_hooks_exist(self):
        """Test that base adapter has all dockable hooks."""
        adapter = GenericAdapter()
        # Check all dockable hooks exist
        assert hasattr(adapter, "supports_dockable")
        assert hasattr(adapter, "create_dockable_widget")
        assert hasattr(adapter, "show_dockable")
        assert hasattr(adapter, "restore_dockable")
        assert hasattr(adapter, "close_dockable")

    def test_base_adapter_dockable_returns_false(self):
        """Test that base adapter dockable methods return False."""
        adapter = GenericAdapter()
        assert adapter.restore_dockable("test") is False
        assert adapter.close_dockable("test") is False

    def test_maya_adapter_has_dockable_methods(self):
        """Test that MayaAdapter has all dockable methods."""
        from auroraview_dcc_shelves.apps.maya import MayaAdapter

        adapter = MayaAdapter()
        assert callable(adapter.create_dockable_widget)
        assert callable(adapter.show_dockable)
        assert callable(adapter.restore_dockable)
        assert callable(adapter.close_dockable)

    def test_nuke_adapter_has_dockable_methods(self):
        """Test that NukeAdapter has all dockable methods."""
        from auroraview_dcc_shelves.apps.nuke import NukeAdapter

        adapter = NukeAdapter()
        assert callable(adapter.create_dockable_widget)
        assert callable(adapter.show_dockable)
        assert callable(adapter.restore_dockable)
        assert callable(adapter.close_dockable)

    def test_houdini_adapter_has_dockable_methods(self):
        """Test that HoudiniAdapter has all dockable methods."""
        from auroraview_dcc_shelves.apps.houdini import HoudiniAdapter

        adapter = HoudiniAdapter()
        assert callable(adapter.create_dockable_widget)
        assert callable(adapter.show_dockable)
        assert callable(adapter.restore_dockable)
        assert callable(adapter.close_dockable)
