# WebView Integration Best Practices

## 问题类型：DCC 应用中的 WebView UI 冻结

### 典型症状
- WebView 窗口显示但无法交互
- DCC 主界面（如 Maya）完全冻结
- 无法点击菜单、移动窗口
- 简单的 WebView 测试正常，但完整应用冻结

---

## 根本原因：重复异步操作导致消息队列堆积

### 反模式 ❌

```python
def _schedule_api_registration(self) -> None:
    """多次重试 - 导致重复注册"""
    delays = [200, 500, 1000, 2000]  # 4 次调用！
    for delay in delays:
        QTimer.singleShot(delay, self._register_api_after_load)
```

**问题**:
- API 注册 4 次
- 前端收到 4 次 "API ready" 事件
- 前端重新加载配置 4 次
- IPC 消息队列堆积
- UI 线程阻塞

### 最佳实践 ✅

```python
def __init__(self):
    self._api_registered = False  # 状态标志

def _schedule_api_registration(self) -> None:
    """单次调用 + 状态防护"""
    delay = 500  # 单次延迟
    QTimer.singleShot(delay, self._register_api_after_load)

def _register_api_after_load(self) -> None:
    # 防护：防止重复注册
    if self._api_registered:
        logger.debug("API already registered, skipping")
        return

    self._api_registered = True  # 立即标记
    # ... 执行注册逻辑
```

**优势**:
- ✅ API 只注册一次
- ✅ 最小化 IPC 消息
- ✅ UI 线程流畅
- ✅ 防止并发调用

---

## 诊断方法：逐步隔离测试法

### 1. 测试基础组件

```python
# 测试 QtWebView 基础功能
webview = QtWebView(parent=dialog, title="Test", width=400, height=300)
webview.show()
# 检查：Maya UI 是否响应？
```

### 2. 测试每个初始化步骤

```python
# 逐步测试，每步间隔 2-3 秒
QTimer.singleShot(2000, step1_create_dialog)
QTimer.singleShot(4000, step2_create_webview)
QTimer.singleShot(6000, step3_load_url)
QTimer.singleShot(8000, step4_bind_api)
# 观察哪一步导致冻结
```

### 3. 测试实际内容加载

```python
# 加载生产环境的前端
webview.load_url("file:///path/to/dist/index.html")
# 检查：是前端问题还是后端问题？
```

### 4. 对比测试

- ✅ 简单测试正常 → 问题在复杂逻辑中
- ✅ 逐步测试正常 → 问题在完整流程中
- ✅ 加载前端正常 → 问题在初始化链中

---

## 核心原则

### 1. 异步操作必须有防护机制

```python
# ❌ 错误：无防护的异步操作
def async_operation(self):
    QTimer.singleShot(100, self._do_something)
    QTimer.singleShot(200, self._do_something)  # 可能重复！

# ✅ 正确：带状态标志的异步操作
def async_operation(self):
    if self._operation_done:
        return
    self._operation_done = True
    QTimer.singleShot(100, self._do_something)
```

### 2. 避免盲目的重试策略

```python
# ❌ 错误：盲目重试
for delay in [100, 200, 500, 1000]:
    QTimer.singleShot(delay, self._retry_operation)

# ✅ 正确：事件驱动
webview.loadFinished.connect(self._on_load_finished)
```

### 3. 使用事件驱动而非定时重试

```python
# ❌ 错误：定时轮询
QTimer.singleShot(500, self._check_if_ready)

# ✅ 正确：信号/事件
webview.loadFinished.connect(self._on_ready)
```

### 4. 日志记录关键状态

```python
logger.info(f"[{operation}] Starting (first time)")  # 标记首次
logger.debug(f"[{operation}] Already done, skipping")  # 标记跳过
```

---

## 修复检查清单

- [ ] 添加状态标志防止重复操作
- [ ] 移除不必要的重试循环
- [ ] 使用信号/事件而非定时器
- [ ] 添加日志记录状态变化
- [ ] 创建逐步诊断脚本
- [ ] 在 DCC 环境中测试
- [ ] 验证 UI 响应性
- [ ] 检查日志确认单次执行

---

## 相关文件

- 修复示例: `src/auroraview_dcc_shelves/app.py` (lines 188-193, 1177-1434)
- 诊断脚本: `tests/diagnose_step_by_step.py`
- 测试脚本: `tests/test_api_registration_fix.py`
