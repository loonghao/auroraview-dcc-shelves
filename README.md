# AuroraView DCC Shelves

[![PyPI version](https://img.shields.io/pypi/v/auroraview-dcc-shelves.svg)](https://pypi.org/project/auroraview-dcc-shelves/)
[![Python versions](https://img.shields.io/pypi/pyversions/auroraview-dcc-shelves.svg)](https://pypi.org/project/auroraview-dcc-shelves/)
[![License](https://img.shields.io/github/license/loonghao/auroraview-dcc-shelves.svg)](https://github.com/loonghao/auroraview-dcc-shelves/blob/main/LICENSE)
[![CI](https://github.com/loonghao/auroraview-dcc-shelves/actions/workflows/pr-checks.yml/badge.svg)](https://github.com/loonghao/auroraview-dcc-shelves/actions/workflows/pr-checks.yml)

[中文文档](README_zh.md)

A dynamic, YAML-configurable tool shelf system for DCC (Digital Content Creation) software, powered by the [AuroraView](https://github.com/loonghao/auroraview) framework.

![DCC Shelves Preview](docs/images/preview.gif)

## ✨ Features

- 🎨 **Modern Web UI** - Beautiful, responsive interface built with Vue 3 and Tailwind CSS
- 📝 **YAML Configuration** - Define your tools and shelves in simple YAML files
- 🔧 **Multi-Tool Support** - Launch Python scripts and external executables
- 🎯 **DCC Integration** - Works with Maya, Houdini, Blender, Nuke, and more
- 🔍 **Search & Filter** - Quickly find tools with real-time search
- 🎛️ **Customizable** - Group tools into shelves, add icons and descriptions

## 📦 Installation

```bash
pip install auroraview-dcc-shelves
```

For Qt integration (required for DCC software):

```bash
pip install auroraview-dcc-shelves[qt]
```

## 🚀 Quick Start

### 1. Create a Configuration File

Create a `shelf_config.yaml` file:

```yaml
shelves:
  - name: "Modeling"
    buttons:
      - name: "Poly Reduce"
        icon: "layers"
        tool_type: "python"
        tool_path: "scripts/poly_reduce.py"
        description: "Reduce polygon count"

      - name: "UV Unwrap"
        icon: "grid"
        tool_type: "python"
        tool_path: "scripts/uv_unwrap.py"
        description: "Automatic UV unwrapping"

  - name: "Utilities"
    buttons:
      - name: "Scene Cleaner"
        icon: "folder"
        tool_type: "python"
        tool_path: "scripts/scene_cleaner.py"
        description: "Clean up unused nodes"
```

### 2. Desktop Mode (Standalone Application)

Run the shelf as a standalone desktop application without any DCC software:

**Command Line:**

```bash
# Basic usage
python -m auroraview_dcc_shelves -c shelf_config.yaml

# With debug mode (press F12 for DevTools)
python -m auroraview_dcc_shelves -c shelf_config.yaml --debug

# Custom window size and title
python -m auroraview_dcc_shelves -c shelf_config.yaml -w 1024 --height 768 -t "My Tools"

# Using installed command
auroraview-shelves -c shelf_config.yaml --debug
dcc-shelves -c shelf_config.yaml --debug
```

**Python API:**

```python
from auroraview_dcc_shelves.apps.desktop import run_desktop

# Simple usage
run_desktop("shelf_config.yaml", debug=True)

# With options
run_desktop(
    config_path="shelf_config.yaml",
    debug=True,
    width=1024,
    height=768,
    title="My Pipeline Tools"
)
```

**CLI Options:**

| Option | Description |
|--------|-------------|
| `-c, --config PATH` | Path to YAML configuration file |
| `-d, --debug` | Enable debug mode with DevTools (F12) |
| `-w, --width INT` | Window width in pixels (default: 800) |
| `--height INT` | Window height in pixels (default: 600) |
| `-t, --title TEXT` | Window title (default: "DCC Shelves") |
| `-v, --verbose` | Enable verbose logging |
| `--version` | Show version and exit |

### 3. Use in DCC Software (Maya, Houdini, etc.)

```python
from auroraview_dcc_shelves import ShelfApp, load_config

config = load_config("/path/to/shelf_config.yaml")
app = ShelfApp(config, title="My Tools")
app.show(app="maya")  # Enable DCC integration
```

## 🔌 Integration Modes

AuroraView DCC Shelves supports two integration modes for DCC applications:

### Qt Mode (Default) - For Dockable Widgets

Best for: **Maya, Houdini, Nuke, 3ds Max**

Uses `QtWebView` for native Qt widget integration. Supports `QDockWidget` docking.

```python
from auroraview_dcc_shelves import ShelfApp, load_config

config = load_config("shelf_config.yaml")
app = ShelfApp(config)
app.show(app="maya", mode="qt")  # Default mode
```

**Features:**
- ✅ Native Qt widget - can be docked, embedded in layouts
- ✅ Managed by Qt's parent-child system
- ✅ Automatic cleanup when parent closes
- ✅ Supports QDockWidget docking

### HWND Mode - For Non-Qt Applications

Best for: **Unreal Engine, or when Qt mode causes issues**

Uses `AuroraView` with HWND for standalone window integration.

```python
from auroraview_dcc_shelves import ShelfApp, load_config

config = load_config("shelf_config.yaml")
app = ShelfApp(config)
app.show(app="maya", mode="hwnd")

# Get HWND for external integration (e.g., Unreal Engine)
hwnd = app.get_hwnd()
if hwnd:
    print(f"Window handle: 0x{hwnd:x}")
```

**Unreal Engine Integration:**

```python
from auroraview_dcc_shelves import ShelfApp, load_config

config = load_config("shelf_config.yaml")
app = ShelfApp(config)
app.show(app="unreal", mode="hwnd")

# Embed into Unreal's Slate UI
hwnd = app.get_hwnd()
if hwnd:
    import unreal
    unreal.parent_external_window_to_slate(hwnd)
```

**Features:**
- ✅ Standalone window with HWND access
- ✅ Can be embedded via HWND APIs
- ✅ Works with non-Qt applications
- ⚠️ Not a true Qt child widget (no QDockWidget docking)

### Mode Comparison

| Feature | Qt Mode (`mode="qt"`) | HWND Mode (`mode="hwnd"`) |
|---------|----------------------|---------------------------|
| Qt Docking | ✅ Supported | ❌ Not supported |
| HWND Access | ⚠️ Limited | ✅ Full access |
| Unreal Engine | ❌ Not recommended | ✅ Recommended |
| Maya/Houdini/Nuke | ✅ Recommended | ⚠️ Works but no docking |
| Parent-child lifecycle | ✅ Automatic | ⚠️ Manual |

## 📖 Configuration Reference

### Button Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | ✅ | Display name of the tool |
| `tool_type` | string | ✅ | `"python"` or `"executable"` |
| `tool_path` | string | ✅ | Path to the script or executable |
| `icon` | string | ❌ | Icon name (see available icons) |
| `args` | list | ❌ | Command line arguments |
| `description` | string | ❌ | Tooltip description |
| `id` | string | ❌ | Unique identifier (auto-generated) |

### Available Icons

`box`, `wrench`, `file-code`, `terminal`, `folder`, `image`, `film`, `music`, `palette`, `layers`, `cpu`, `database`, `globe`, `settings`, `zap`, `package`, `grid`, `pencil`

## 🎨 Color Scheme & Visual Design System

AuroraView DCC Shelves uses a modern dark theme inspired by Apple's design language, creating a professional and immersive experience for DCC artists.

### Core Color Palette

| Color | Hex / Value | Usage |
|-------|-------------|-------|
| **Background Dark** | `#0d0d0d` | Main background, dialogs |
| **Background Light** | `#1d1d1f` | Gradient top, elevated surfaces |
| **Text Primary** | `#f5f5f7` | Primary text, headings |
| **Text Secondary** | `rgba(255,255,255,0.6)` | Descriptions, labels |
| **Text Muted** | `rgba(255,255,255,0.4)` | Inactive states |

### Brand & Accent Colors

| Color | Hex | Usage |
|-------|-----|-------|
| **Brand 400** | `#34d399` | Success states, active indicators |
| **Brand 500** | `#10b981` | Primary brand color |
| **Brand 600** | `#059669` | Brand hover states |
| **Accent 400** | `#22d3ee` | Highlights, links |
| **Accent 500** | `#06b6d4` | Secondary accent |

### Status Colors

| Status | Color | Usage |
|--------|-------|-------|
| **Info** | `text-blue-400` | Information messages |
| **Warning** | `text-amber-400` | Warning alerts |
| **Error** | `text-red-400` | Error states |
| **Success** | `text-emerald-400` | Success confirmations |
| **Running** | `bg-orange-500` | Tool execution indicator |

### UI Component Styles

#### Glassmorphism Effects

```css
/* Primary glass panel */
.glass {
  background: rgba(28, 28, 30, 0.72);
  backdrop-filter: blur(20px) saturate(180%);
}

/* Subtle glass panel */
.glass-subtle {
  background: rgba(44, 44, 46, 0.6);
  backdrop-filter: blur(10px);
}
```

#### Tool Button States

| State | Style |
|-------|-------|
| Default | `bg-white/[0.03]` with transparent border |
| Hover | `bg-white/[0.08]` with `border-white/10` |
| Active | `scale-95` transform |

#### Design Principles

1. **Dark-first Design** - Optimized for long working sessions in DCCs
2. **Subtle Animations** - Spring-based transitions for natural feel
3. **Minimal Chrome** - Focus on content, not UI elements
4. **Accessibility** - Clear contrast ratios for readability

## 🛠️ Development

### Setup

```bash
# Clone the repository
git clone https://github.com/loonghao/auroraview-dcc-shelves.git
cd auroraview-dcc-shelves

# Install dependencies
uv sync --dev

# Install frontend dependencies
npm install
```

### Running Tests

```bash
# Run Python tests
uvx nox -s pytest

# Run linting
uvx nox -s lint

# Format code
uvx nox -s format
```

### Building

```bash
# Build frontend
npm run build

# Build Python package
uv build
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## 🔗 Related Projects

- [AuroraView](https://github.com/loonghao/auroraview) - The WebView framework powering this project
- [AuroraView Maya Outliner](https://github.com/loonghao/auroraview-maya-outliner) - Another AuroraView-based tool

## 📷 Image Credits

The banner image used in this project is for **demonstration purposes only** and is **not for commercial use**.

- Source: [Huaban](https://huaban.com/pins/4758761487)

If there is any copyright infringement, please contact us and we will remove it immediately.
