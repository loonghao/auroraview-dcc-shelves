"""Constants and configuration values for DCC Shelves UI.

This module contains window configuration, timer settings, and other
constants used by the ShelfApp.
"""

from __future__ import annotations

from typing import Literal

# =============================================================================
# Window Configuration
# Keep in sync with frontend CSS (App.tsx: min-w-[280px] max-w-[480px])
# NOTE: These are CONTENT sizes, not window sizes. Qt window decorations
# (title bar, borders) will add extra pixels. The frontend should receive
# exactly these pixel values as the WebView viewport size.
# =============================================================================
MAIN_WINDOW_CONFIG = {
    "min_width": 400,
    "min_height": 400,
    "max_width": 700,  # 0 = no limit, allow user to resize freely
    "max_height": 0,  # 0 = no limit
    "default_width": 500,
    "default_height": 700,
}

SETTINGS_WINDOW_CONFIG = {
    "min_width": 400,
    "min_height": 500,
    "max_width": 600,
    "max_height": 800,
    "default_width": 520,
    "default_height": 650,
}

# Type alias for integration mode
# - "qt": Uses QtWebView for Qt widget integration (recommended)
#         Uses createWindowContainer for native Qt layout integration with automatic resize.
# - "hwnd": Uses AuroraView with HWND for non-Qt apps (Unreal Engine)
IntegrationMode = Literal["qt", "hwnd"]

# =============================================================================
# DCC Timer Settings (DEPRECATED)
# Timer settings are now managed by DCC adapters (apps/*.py)
# This dict is kept for backward compatibility only.
# Use: get_adapter(app_name).timer_interval_ms instead
# =============================================================================
DCC_TIMER_SETTINGS: dict[str, dict[str, int]] = {
    "maya": {"interval_ms": 16},  # Maya: 60 FPS, responsive UI
    "houdini": {"interval_ms": 50},  # Houdini: 20 FPS, reduced overhead
    "nuke": {"interval_ms": 32},  # Nuke: 30 FPS, balanced
    "3dsmax": {"interval_ms": 32},  # 3ds Max: 30 FPS
    "max": {"interval_ms": 32},  # Alias for 3ds Max
    "unreal": {"interval_ms": 16},  # Unreal: 60 FPS
    "default": {"interval_ms": 16},  # Default: 60 FPS
}

# =============================================================================
# Icon Extensions
# =============================================================================
ICON_EXTENSIONS = [".svg", ".png", ".ico", ".jpg", ".jpeg", ".gif", ".webp"]
