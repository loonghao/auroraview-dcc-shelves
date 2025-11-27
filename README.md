# AuroraView DCC Shelves

[![PyPI version](https://img.shields.io/pypi/v/auroraview-dcc-shelves.svg)](https://pypi.org/project/auroraview-dcc-shelves/)
[![Python versions](https://img.shields.io/pypi/pyversions/auroraview-dcc-shelves.svg)](https://pypi.org/project/auroraview-dcc-shelves/)
[![License](https://img.shields.io/github/license/loonghao/auroraview-dcc-shelves.svg)](https://github.com/loonghao/auroraview-dcc-shelves/blob/main/LICENSE)
[![CI](https://github.com/loonghao/auroraview-dcc-shelves/actions/workflows/pr-checks.yml/badge.svg)](https://github.com/loonghao/auroraview-dcc-shelves/actions/workflows/pr-checks.yml)

[中文文档](README_zh.md)

A dynamic, YAML-configurable tool shelf system for DCC (Digital Content Creation) software, powered by the [AuroraView](https://github.com/loonghao/auroraview) framework.

![DCC Shelves Preview](docs/images/preview.png)

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

### 2. Launch the Shelf

```python
from auroraview_dcc_shelves import ShelfApp, load_config

# Load configuration
config = load_config("shelf_config.yaml")

# Create and show the shelf
app = ShelfApp(config)
app.show()
```

### 3. Use in Maya

```python
from auroraview_dcc_shelves import ShelfApp, load_config

config = load_config("/path/to/shelf_config.yaml")
app = ShelfApp(config, title="My Tools")
app.show()
```

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

