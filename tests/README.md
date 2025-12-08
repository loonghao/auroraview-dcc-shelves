# DCC Shelves UI Tests

This directory contains automated UI tests for the DCC Shelves frontend using the AuroraView testing framework.

## Overview

The tests use the **actual project frontend** (not mock HTML) to ensure real-world functionality is tested. Tests can run against either:
- **Vite dev server** (`npm run dev`) - recommended for development
- **Production build** (`dist/`) - for CI/CD

## Test Structure

| File | Description |
|------|-------------|
| `conftest.py` | Pytest fixtures and configuration |
| `test_ui_main_layout.py` | Main layout structure tests (banner, search, tabs, etc.) |
| `test_ui_interactions.py` | User interaction tests (clicks, hover, keyboard) |
| `test_ui_dialogs.py` | Dialog/modal tests (create tool, settings, etc.) |
| `test_ui_console.py` | Console tab functionality tests |
| `test_ui_i18n.py` | Internationalization tests (English/Chinese) |
| `test_ui_zoom.py` | Zoom controls tests |
| `test_ui_simple.py` | Simple standalone test script (no pytest) |

## Prerequisites

1. **Build the frontend** (if not using dev server):
   ```bash
   npm run build
   ```

2. **Or start the dev server**:
   ```bash
   npm run dev
   ```

3. **Install test dependencies**:
   ```bash
   uv pip install pytest
   ```

## Running Tests

### Using pytest (recommended)

```bash
# Run all UI tests
uv run python -m pytest tests/test_ui_*.py -v

# Run specific test file
uv run python -m pytest tests/test_ui_main_layout.py -v

# Run specific test class
uv run python -m pytest tests/test_ui_main_layout.py::TestBanner -v

# Run specific test
uv run python -m pytest tests/test_ui_main_layout.py::TestBanner::test_banner_exists -v
```

### Using the test runner script

```bash
# Run all tests
python tests/run_tests.py

# Run with verbose output
python tests/run_tests.py -v

# Run specific category
python tests/run_tests.py --layout
python tests/run_tests.py --interactions
python tests/run_tests.py --dialogs
python tests/run_tests.py --i18n

# Auto-start dev server
python tests/run_tests.py --start-server
```

### Using the simple test script (standalone)

```bash
# Run without pytest
python tests/test_ui_simple.py
```

## Test Coverage

### Main Layout (`test_ui_main_layout.py`)
- ✅ Banner (title, icon, subtitle)
- ✅ Search bar (input, placeholder, typing)
- ✅ Shelf tabs (navigation)
- ✅ Tool grid (buttons, icons)
- ✅ Bottom panel (Detail/Console tabs)
- ✅ User Tools panel
- ✅ Settings button
- ✅ Layout structure (flexbox/grid)

### Interactions (`test_ui_interactions.py`)
- ✅ Tool button click/hover
- ✅ Search filtering
- ✅ Tab navigation
- ✅ Context menu
- ✅ Keyboard navigation
- ✅ State persistence

### Dialogs (`test_ui_dialogs.py`)
- ✅ Create Tool dialog
- ✅ Settings dialog
- ✅ Confirmation dialogs
- ✅ Dialog accessibility (ARIA)
- ✅ Dialog animations

### Console (`test_ui_console.py`)
- ✅ Console tab switching
- ✅ Log display
- ✅ Clear button
- ✅ Scrollable output

### i18n (`test_ui_i18n.py`)
- ✅ Language detection
- ✅ English translations
- ✅ Chinese translations
- ✅ Language switching
- ✅ Tool name translations

### Zoom (`test_ui_zoom.py`)
- ✅ Zoom controls visibility
- ✅ Zoom in/out buttons
- ✅ Zoom reset
- ✅ Keyboard shortcuts
- ✅ Auto zoom
- ✅ Zoom persistence

## Mock API

Tests use a mock `TestShelfAPI` class that provides:
- `get_config()` - Returns test configuration with sample tools
- `launch_tool()` - Logs tool launch (no actual execution)
- `get_user_tools()` - Returns empty user tools
- `save_user_tool()` / `delete_user_tool()` - Mock operations
- `create_window()` / `close_window()` - Mock window operations

## Known Issues

1. **WebView close panic**: The WebView may panic when closing during tests. This is handled by using module-scoped fixtures and deferring cleanup to process exit.

2. **Test isolation**: Tests within the same module share a WebView instance to avoid close/reopen issues.

3. **Timing**: Some tests require delays for React rendering. Adjust `time.sleep()` values if tests are flaky.

## CI/CD Integration

For CI/CD environments:

1. **Build frontend first**:
   ```yaml
   - run: npm ci
   - run: npm run build
   ```

2. **Run tests**:
   ```yaml
   - run: uv run python -m pytest tests/test_ui_*.py -v --tb=short
   ```

3. **Note**: Tests require a display. Use `xvfb` on Linux:
   ```yaml
   - run: xvfb-run uv run python -m pytest tests/test_ui_*.py
   ```

## Writing New Tests

1. Import the fixtures from `conftest.py`:
   ```python
   from auroraview import WebView

   def test_example(shelf_webview: WebView):
       result = shelf_webview.eval_js("document.title")
       assert result == "DCC Shelves"
   ```

2. Use `eval_js()` for JavaScript assertions:
   ```python
   def test_element_exists(shelf_webview: WebView):
       exists = shelf_webview.eval_js("document.querySelector('#myId') !== null")
       assert exists is True
   ```

3. Add delays for async operations:
   ```python
   import time

   def test_async_action(shelf_webview: WebView):
       shelf_webview.eval_js("someAsyncAction()")
       time.sleep(0.5)  # Wait for action to complete
       result = shelf_webview.eval_js("getResult()")
   ```
