# Case Study: Maya UI 冻结问题修复

## 问题描述

**日期**: 2025-12-05
**环境**: Maya 2024 + AuroraView DCC Shelves
**症状**: 启动 DCC Shelves 后，Maya UI 完全冻结，无法交互

---

## 诊断过程

### 阶段 1: 验证基础功能

**测试**: 简单的 QtWebView 创建和显示

```python
webview = QtWebView(parent=dialog, title="Test", width=400, height=300)
webview.show()
```

**结果**: ✅ 成功 - Maya UI 响应正常

**结论**: 问题不在 QtWebView 基础功能中

---

### 阶段 2: 逐步隔离测试

**测试**: 分步执行 DCC Shelves 初始化流程

```python
Step 1: Create dialog
Step 2: Create QtWebView
Step 3: Load URL (about:blank)
Step 4: Create ShelfAPI
Step 5: Bind API
Step 6: Execute JavaScript
```

**结果**: ✅ 所有步骤成功 - Maya UI 响应正常

**结论**: 问题不在单个操作中，而在完整流程的某个环节

---

### 阶段 3: 测试实际前端加载

**测试**: 加载生产环境的前端 HTML

```python
webview.load_url("file:///C:/github/auroraview-dcc-shelves/dist/index.html")
```

**结果**: ✅ 成功 - Maya UI 响应正常

**结论**: 问题不在前端 JavaScript 代码中

---

### 阶段 4: 代码审查

**发现**: `_schedule_api_registration()` 调用了 4 次 `_register_api_after_load()`

```python
def _schedule_api_registration(self) -> None:
    delays = [200, 500, 1000, 2000]  # 4 次！
    for delay in delays:
        QTimer.singleShot(delay, self._register_api_after_load)
```

每次调用都会:
1. 重新绑定 API
2. 注入大量 JavaScript 代码
3. 通知前端 "API ready"

**根本原因**:
- 前端收到 4 次 "API ready" 事件
- 前端重新加载配置 4 次
- IPC 消息队列堆积
- UI 线程被阻塞

---

## 解决方案

### 修复 1: 添加状态标志

```python
def __init__(self):
    # API registration state tracking (防止重复注册)
    self._api_registered = False
```

### 修复 2: 添加防护逻辑

```python
def _register_api_after_load(self) -> None:
    # Guard: Prevent multiple registrations
    if self._api_registered:
        logger.debug("[_register_api_after_load] API already registered, skipping")
        return

    self._api_registered = True
    logger.info("[_register_api_after_load] Starting API registration (first time)")
    # ... 执行注册逻辑
```

### 修复 3: 简化调度逻辑

```python
def _schedule_api_registration(self) -> None:
    """Schedule API registration after page load using QTimer.

    FIXED: Only schedule once instead of multiple times.
    """
    from qtpy.QtCore import QTimer

    delay = 500  # 单次延迟
    QTimer.singleShot(delay, self._register_api_after_load)

    logger.debug(f"Scheduled single API registration at {delay}ms")
```

---

## 修复效果

### 修复前 ❌
- API 注册 4 次
- 前端重新加载配置 4 次
- 大量 IPC 消息堆积
- Maya UI 冻结

### 修复后 ✅
- API 注册 1 次
- 前端加载配置 1 次
- 最小化 IPC 消息
- Maya UI 流畅响应

---

## 经验教训

### 1. 诊断方法
- ✅ 逐步隔离测试法非常有效
- ✅ 对比简单测试和完整流程
- ✅ 代码审查找出重复操作

### 2. 设计原则
- ❌ 避免盲目的重试策略
- ✅ 使用状态标志防止重复
- ✅ 优先使用事件驱动而非定时器
- ✅ 添加日志记录关键状态

### 3. 性能优化
- 异步操作要有防护机制
- 避免不必要的重复调用
- 最小化 IPC 消息数量
- 保持 UI 线程流畅

---

## 相关文件

- **修复代码**: `src/auroraview_dcc_shelves/app.py`
  - Line 188-193: 添加 `_api_registered` 标志
  - Line 1177-1195: 添加防护逻辑
  - Line 1417-1434: 简化调度逻辑

- **诊断脚本**:
  - `tests/diagnose_step_by_step.py`
  - `tests/test_api_registration_fix.py`

- **文档**:
  - `tests/fix_api_registration.md`
  - `.augment/rules/webview-integration-best-practices.md`
