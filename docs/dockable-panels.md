# Dockable Panels

AuroraView DCC Shelves supports native dockable panels in Maya, Houdini, and Nuke. This allows the shelf UI to be docked into the DCC's native panel system for a more integrated experience.

## Quick Start

```python
from auroraview_dcc_shelves import ShelfApp, load_config

config = load_config("shelf_config.yaml")
app = ShelfApp(config)

# Show as dockable panel (native DCC docking)
app.show(app="maya", dockable=True)

# Or show as floating window (default)
app.show(app="maya", dockable=False)
```

## DCC-Specific Behavior

### Maya

Maya uses `workspaceControl` for dockable panels:

```python
# Basic dockable panel
app.show(app="maya", dockable=True)

# The panel can be:
# - Docked to left/right/top/bottom of Maya window
# - Tabbed with other panels
# - Floated as a separate window
```

**Features:**
- Native Maya workspace integration
- State persistence across sessions
- Tab support with other Maya panels

### Houdini

Houdini creates a floating tool window by default:

```python
# Floating tool window (stays on top of Houdini)
app.show(app="houdini", dockable=True)
```

**Features:**
- Qt.Tool window flag for proper parenting
- Stays on top of Houdini main window
- Qt6 performance optimizations applied

**Note:** Full Python Panel integration (docking into Houdini's pane system) requires additional setup with `hou.pypanel` interfaces.

### Nuke

Nuke uses `nukescripts.panels` for panel registration:

```python
# Dockable panel in Nuke
app.show(app="nuke", dockable=True)
```

**Features:**
- Native Nuke panel integration
- Can be added to Nuke's pane system
- Tab support with other Nuke panels

## API Reference

### ShelfApp.show()

```python
def show(
    self,
    debug: bool = False,
    app: str | None = None,
    mode: IntegrationMode = "qt",
    dockable: bool = False,
) -> None:
```

**Parameters:**
- `debug`: Enable developer tools (F12)
- `app`: DCC application name ("maya", "houdini", "nuke")
- `mode`: Integration mode ("qt" or "hwnd")
- `dockable`: If True, create a dockable panel

### DCCAdapter Dockable Hooks

Each DCC adapter implements these hooks:

```python
class DCCAdapter:
    def supports_dockable(self) -> bool:
        """Check if this DCC supports dockable panels."""
        
    def create_dockable_widget(
        self,
        widget: QWidget,
        title: str,
        object_name: str,
    ) -> Any:
        """Create a dockable panel containing the widget."""
        
    def show_dockable(
        self,
        widget: QWidget,
        title: str,
        object_name: str,
        **kwargs,
    ) -> bool:
        """Show a widget as a dockable panel."""
        
    def restore_dockable(self, object_name: str) -> bool:
        """Restore a previously created dockable panel."""
        
    def close_dockable(self, object_name: str) -> bool:
        """Close and cleanup a dockable panel."""
```

## Fallback Behavior

If dockable mode is requested but not supported:

1. A warning is logged
2. The shelf falls back to floating window mode
3. All functionality remains available

```python
# If DCC doesn't support docking, this falls back to floating window
app.show(app="unknown_dcc", dockable=True)
# Warning: Dockable mode requested but unknown_dcc does not support docking.
```

## Best Practices

1. **Use dockable=True for production**: Native docking provides better UX
2. **Use dockable=False for development**: Easier to debug floating windows
3. **Test in each DCC**: Docking behavior varies between applications
4. **Handle restore**: Maya may call restore when loading workspaces

