# Optimization Opportunities

基于 Maya UI 冻结问题修复的经验，以下是代码库中可以继续优化的地方。

---

## 1. Geometry Fix 重复调用 ⚠️

### 当前实现

<augment_code_snippet path="src/auroraview_dcc_shelves/app.py" mode="EXCERPT">
```python
def _schedule_geometry_fixes(self) -> None:
    delays = [100, 500, 1000, 2000]  # 4 次调用！
    if self._adapter:
        delays = self._adapter.get_geometry_fix_delays()
    
    for delay in delays:
        QTimer.singleShot(delay, force_geometry)
```
</augment_code_snippet>

### 问题
- 与 API 注册问题类似，多次调用 `force_geometry`
- 可能导致不必要的 UI 重绘
- 没有状态标志防止重复

### 建议优化

```python
def __init__(self):
    self._geometry_fixed = False  # 添加状态标志

def _schedule_geometry_fixes(self) -> None:
    def force_geometry() -> None:
        if self._geometry_fixed:
            logger.debug("Geometry already fixed, skipping")
            return
        
        # 执行几何修复
        # ...
        
        # 标记为已修复（可选：只在最后一次标记）
        # self._geometry_fixed = True

    # 使用事件驱动而非多次重试
    # 或者只在最后一次延迟后标记为完成
    delays = self._adapter.get_geometry_fix_delays() if self._adapter else [100, 500, 1000, 2000]
    
    for i, delay in enumerate(delays):
        is_last = (i == len(delays) - 1)
        QTimer.singleShot(delay, lambda last=is_last: force_geometry_with_flag(last))
```

---

## 2. Deferred Initialization Chain 可以简化 💡

### 当前实现

<augment_code_snippet path="src/auroraview_dcc_shelves/ui/modes/qt.py" mode="EXCERPT">
```python
def _deferred_init_step1():
    # ...
    QTimer.singleShot(50, _deferred_init_step2)

def _deferred_init_step2():
    # ...
    QTimer.singleShot(10, _deferred_init_step3)

def _deferred_init_step3():
    # ...
    QTimer.singleShot(10, _deferred_init_step4)
# ... 5 个步骤
```
</augment_code_snippet>

### 问题
- 嵌套的回调链难以维护
- 每个步骤都有固定延迟，可能不必要
- 错误处理分散在各个步骤中

### 建议优化

```python
def _deferred_init_chain(self) -> None:
    """使用队列模式简化初始化链"""
    steps = [
        ("Connect signals", self._connect_qt_signals, 50),
        ("Register events", self._register_window_events, 10),
        ("Setup state", self._setup_shared_state, 10),
        ("Register commands", self._register_commands, 10),
        ("Schedule fixes", lambda: (self._schedule_geometry_fixes(), self._schedule_api_registration()), 10),
        ("Adapter on_show", lambda: self._adapter.on_show(self) if self._adapter else None, 10),
    ]
    
    def run_step(index: int) -> None:
        if index >= len(steps):
            logger.info("Deferred initialization complete!")
            return
        
        name, func, delay = steps[index]
        try:
            logger.debug(f"Step {index + 1}: {name}")
            func()
        except Exception as e:
            logger.warning(f"Step {index + 1} ({name}) failed: {e}")
        
        # Schedule next step
        if index + 1 < len(steps):
            next_delay = steps[index + 1][2]
            QTimer.singleShot(next_delay, lambda: run_step(index + 1))
    
    # Start chain
    QTimer.singleShot(steps[0][2], lambda: run_step(0))
```

---

## 3. 使用 loadFinished 信号替代定时器 ✅

### 当前实现

<augment_code_snippet path="src/auroraview_dcc_shelves/ui/modes/dockable.py" mode="EXCERPT">
```python
if hasattr(self._webview, "loadFinished"):
    self._webview.loadFinished.connect(_swap_to_webview)
else:
    QTimer.singleShot(300, lambda: _swap_to_webview(True))
```
</augment_code_snippet>

### 优点
- ✅ 已经使用了事件驱动模式
- ✅ 有 fallback 机制

### 建议
- 将这个模式应用到 API 注册中
- 考虑在 QtWebView 中添加 `loadFinished` 信号

---

## 4. Timer Interval 配置可以动态调整 🎯

### 当前实现

```python
timer_interval_ms: int = 16  # 60 FPS 固定
```

### 建议优化

```python
class AdaptiveTimerConfig:
    """自适应定时器配置"""
    
    def __init__(self):
        self.base_interval = 16  # 60 FPS
        self.idle_interval = 100  # 空闲时降低频率
        self.busy_interval = 8   # 繁忙时提高频率
        self._is_busy = False
    
    def get_interval(self) -> int:
        return self.busy_interval if self._is_busy else self.base_interval
    
    def set_busy(self, busy: bool) -> None:
        self._is_busy = busy
```

**使用场景**:
- 页面加载时使用高频率
- 空闲时降低频率节省 CPU
- 用户交互时提高响应性

---

## 5. 批量操作可以合并 🔄

### 当前模式

```python
# 多次单独调用
webview.eval_js("script1")
webview.eval_js("script2")
webview.eval_js("script3")
```

### 建议优化

```python
class BatchedOperations:
    """批量操作管理器"""
    
    def __init__(self, webview):
        self._webview = webview
        self._pending_scripts = []
        self._flush_timer = None
    
    def queue_js(self, script: str) -> None:
        """队列 JavaScript 执行"""
        self._pending_scripts.append(script)
        
        # 延迟刷新，允许批量累积
        if self._flush_timer:
            self._flush_timer.stop()
        
        self._flush_timer = QTimer()
        self._flush_timer.setSingleShot(True)
        self._flush_timer.timeout.connect(self._flush)
        self._flush_timer.start(10)  # 10ms 批量窗口
    
    def _flush(self) -> None:
        """刷新所有待处理的脚本"""
        if not self._pending_scripts:
            return
        
        # 合并所有脚本
        combined = ";\n".join(self._pending_scripts)
        self._webview.eval_js(combined)
        self._pending_scripts.clear()
```

---

## 优先级排序

### 🔴 高优先级
1. **Geometry Fix 添加状态标志** - 防止重复操作
2. **API 注册使用 loadFinished 信号** - 事件驱动替代定时器

### 🟡 中优先级
3. **简化 Deferred Init Chain** - 提高可维护性
4. **批量操作合并** - 减少 IPC 消息

### 🟢 低优先级
5. **自适应 Timer Interval** - 性能优化

---

## 实施建议

1. **先修复高优先级问题** - 防止潜在的 UI 冻结
2. **逐步重构** - 每次只改一个模块
3. **添加测试** - 确保修改不破坏现有功能
4. **记录经验** - 更新最佳实践文档

---

## 相关文档

- [WebView Integration Best Practices](./webview-integration-best-practices.md)
- [Quick Reference: Async Operations](./quick-reference-async-operations.md)
- [Case Study: Maya UI Freeze Fix](./case-study-maya-ui-freeze-fix.md)

