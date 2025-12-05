# Qt5/Qt6 兼容性优化指南

**问题**: Houdini (PySide6/Qt6) 和 Substance Painter (PySide6/Qt6) 的界面行为与 Maya (PySide2/Qt5) 不一致

**目标**: 统一 Qt5 和 Qt6 环境下的 WebView 行为

---

## 🔍 当前架构分析

### 已有的兼容层

**位置**: `python/auroraview/integration/qt/_compat.py`

**功能**:
- ✅ Qt 版本检测 (`is_qt6()`, `is_qt5()`)
- ✅ HWND 样式准备 (`prepare_hwnd_for_container()`)
- ✅ 容器创建 (`create_container_widget()`)
- ✅ Qt6 特定设置 (`post_container_setup()`)

**Qt6 特定优化**:
```python
if is_qt6():
    container.setAttribute(QtCore.WA_NativeWindow, True)
    container.setAttribute(QtCore.WA_InputMethodEnabled, True)
    container.setContentsMargins(0, 0, 0, 0)
    container.setAttribute(QtCore.WA_OpaquePaintEvent, True)
```

### DCC 适配器配置

**Houdini** (`apps/houdini.py`):
```python
QtConfig(
    init_delay_ms=100,           # Qt6 需要更长初始化时间
    timer_interval_ms=50,        # 20 FPS
    geometry_fix_delays=[100, 300, 600, 1000, 2000],  # 更多延迟
    force_opaque_window=True,    # Qt6 性能优化
    disable_translucent=True,    # 避免透明窗口性能问题
    is_qt6=True,
)
```

**Substance Painter** (`apps/substance_painter.py`):
```python
QtConfig(
    init_delay_ms=50,
    timer_interval_ms=32,        # 30 FPS
    geometry_fix_delays=[50, 150, 300, 500, 1000],
    force_opaque_window=True,
    disable_translucent=True,
    is_qt6=True,
)
```

---

## 🐛 常见 Qt5/Qt6 差异问题

### 1. 窗口样式和透明度

**问题**: Qt6 的半透明窗口性能显著下降

**解决方案**:
```python
# Qt6 强制不透明
if is_qt6():
    dialog.setAttribute(Qt.WA_OpaquePaintEvent, True)
    dialog.setAttribute(Qt.WA_TranslucentBackground, False)
    dialog.setAttribute(Qt.WA_NoSystemBackground, False)
```

### 2. createWindowContainer 行为差异

**问题**: Qt6 对窗口容器的处理更严格

**解决方案**:
```python
# Qt6 需要显式设置 WA_NativeWindow
if is_qt6():
    container.setAttribute(QtCore.WA_NativeWindow, True)
    # 10ms 延迟确保窗口正确附加
    time.sleep(0.01)
    QApplication.processEvents()
```

### 3. 窗口标志差异

**问题**: Qt6 的 Qt.Tool 行为与 Qt5 不同

**Houdini 解决方案**:
```python
# Qt.Tool 确保窗口保持在父窗口之上
dialog.setWindowFlags(
    Qt.Tool | Qt.WindowTitleHint | 
    Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint
)
```

### 4. 事件处理差异

**问题**: Qt6 重写了事件系统，需要更多 processEvents

**解决方案**:
```python
if is_qt6():
    QApplication.processEvents()
    time.sleep(0.01)
    QApplication.processEvents()
```

---

## 🎯 优化建议

### 优先级 1: 统一初始化流程 🔴

**问题**: Qt5 和 Qt6 的初始化延迟不一致

**建议**:
```python
def get_optimal_init_delay() -> int:
    """根据 Qt 版本返回最优初始化延迟"""
    if is_qt6():
        # Qt6 需要更长时间初始化
        return 100  # Houdini
    else:
        # Qt5 可以更快
        return 10   # Maya
```

### 优先级 2: 统一几何修复策略 🔴

**问题**: 不同 DCC 的 geometry_fix_delays 差异很大

**当前状态**:
- Maya (Qt5): `[100, 500, 1000, 2000]`
- Houdini (Qt6): `[100, 300, 600, 1000, 2000]`
- Substance Painter (Qt6): `[50, 150, 300, 500, 1000]`

**建议**: 基于我们的优化经验，使用状态标志后可以简化：
```python
def get_geometry_fix_delays() -> list[int]:
    """根据 Qt 版本返回几何修复延迟"""
    if is_qt6():
        # Qt6 需要更多中间延迟
        return [50, 150, 300, 600, 1000]
    else:
        # Qt5 标准延迟
        return [100, 500, 1000]
```

### 优先级 3: 添加 Qt6 特定诊断 🟡

**建议**: 创建 Qt6 诊断工具

```python
def diagnose_qt6_issues(dialog: QDialog, webview: QWidget) -> dict:
    """诊断 Qt6 特定问题"""
    issues = []
    
    # 检查透明度设置
    if dialog.testAttribute(Qt.WA_TranslucentBackground):
        issues.append("WARNING: Translucent background enabled (slow in Qt6)")
    
    # 检查不透明设置
    if not dialog.testAttribute(Qt.WA_OpaquePaintEvent):
        issues.append("WARNING: OpaquePaintEvent not set (recommended for Qt6)")
    
    # 检查窗口标志
    flags = dialog.windowFlags()
    if not (flags & Qt.Tool):
        issues.append("INFO: Not using Qt.Tool flag (may not stay on top)")
    
    return {
        "qt_version": get_qt_info(),
        "issues": issues,
        "recommendations": _get_qt6_recommendations(issues)
    }
```

---

## 📋 实施计划

### 阶段 1: 增强兼容层 (高优先级)

1. **添加 Qt 版本特定配置工厂**
   ```python
   # python/auroraview/integration/qt/_compat.py
   def create_optimal_qt_config(dcc_name: str) -> QtConfig:
       """根据 DCC 和 Qt 版本创建最优配置"""
       pass
   ```

2. **统一窗口样式应用**
   ```python
   def apply_window_styles(dialog: QDialog, force_opaque: bool = None) -> None:
       """应用 Qt 版本特定的窗口样式"""
       if force_opaque is None:
           force_opaque = is_qt6()
       # ...
   ```

### 阶段 2: 更新适配器 (中优先级)

1. **使用统一的配置工厂**
2. **移除重复的 Qt6 检测代码**
3. **标准化窗口标志设置**

### 阶段 3: 添加诊断工具 (低优先级)

1. **Qt6 问题诊断器**
2. **性能对比工具**
3. **自动化测试**

---

## 🔗 相关文档

- [Qt Compatibility Layer](.../python/auroraview/integration/qt/_compat.py)
- [Houdini Adapter](.../src/auroraview_dcc_shelves/apps/houdini.py)
- [Substance Painter Adapter](.../src/auroraview_dcc_shelves/apps/substance_painter.py)
- [Optimization Changelog](./OPTIMIZATION_CHANGELOG.md)

---

**维护者**: AuroraView Team  
**最后更新**: 2025-12-05

