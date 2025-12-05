---
type: "always_apply"
---

# Quick Reference: 异步操作最佳实践

## 核心模式

### 1. 状态标志模式 (State Flag Pattern)

```python
class MyClass:
    def __init__(self):
        self._operation_done = False  # 状态标志

    def async_operation(self):
        # 防护：防止重复执行
        if self._operation_done:
            logger.debug("Operation already done, skipping")
            return

        # 立即标记，防止并发调用
        self._operation_done = True
        logger.info("Starting operation (first time)")

        # 执行实际操作
        self._do_work()
```

**使用场景**:
- API 注册
- 资源初始化
- 一次性配置加载

---

### 2. 事件驱动模式 (Event-Driven Pattern)

```python
# ❌ 错误：定时轮询
def init_webview(self):
    QTimer.singleShot(500, self._check_if_ready)
    QTimer.singleShot(1000, self._check_if_ready)
    QTimer.singleShot(2000, self._check_if_ready)

# ✅ 正确：事件驱动
def init_webview(self):
    self.webview.loadFinished.connect(self._on_ready)
```

**使用场景**:
- 页面加载完成
- 资源准备就绪
- 用户交互响应

---

### 3. 单次延迟模式 (Single Delay Pattern)

```python
# ❌ 错误：多次重试
def schedule_operation(self):
    for delay in [100, 200, 500, 1000]:
        QTimer.singleShot(delay, self._operation)

# ✅ 正确：单次延迟 + 状态防护
def schedule_operation(self):
    delay = 500  # 合理的单次延迟
    QTimer.singleShot(delay, self._operation)
```

**使用场景**:
- 延迟初始化
- 等待资源准备
- UI 更新延迟

---

## 常见反模式

### ❌ 反模式 1: 无防护的重复调用

```python
def init(self):
    self._register_api()
    QTimer.singleShot(100, self._register_api)
    QTimer.singleShot(200, self._register_api)
    # 问题：API 注册 3 次！
```

### ❌ 反模式 2: 盲目的重试循环

```python
def retry_operation(self):
    for i in range(10):  # 重试 10 次
        QTimer.singleShot(i * 100, self._try_operation)
    # 问题：可能第一次就成功了，后面 9 次都是浪费
```

### ❌ 反模式 3: 缺少状态跟踪

```python
def async_load(self):
    QTimer.singleShot(500, self._load_data)
    # 问题：无法知道是否已加载，可能被多次调用
```

---

## 诊断工具模板

### 逐步测试模板

```python
def step1():
    logger.info("Step 1: Create component")
    # ... 创建组件
    QTimer.singleShot(2000, step2)

def step2():
    logger.info("Step 2: Initialize")
    # ... 初始化
    QTimer.singleShot(2000, step3)

def step3():
    logger.info("Step 3: Load content")
    # ... 加载内容
    logger.info("All steps complete!")

# 启动
QTimer.singleShot(1000, step1)
```

### 状态检查模板

```python
def check_state(self):
    logger.info("=" * 60)
    logger.info("STATE CHECK")
    logger.info("=" * 60)
    logger.info(f"Operation done: {self._operation_done}")
    logger.info(f"API registered: {self._api_registered}")
    logger.info(f"Content loaded: {self._content_loaded}")
    logger.info("=" * 60)
```

---

## 检查清单

### 设计阶段
- [ ] 是否需要状态标志？
- [ ] 能否使用事件驱动？
- [ ] 延迟时间是否合理？
- [ ] 是否有防护机制？

### 实现阶段
- [ ] 添加状态标志
- [ ] 在操作开始时立即标记
- [ ] 添加防护检查
- [ ] 添加日志记录

### 测试阶段
- [ ] 测试单次调用
- [ ] 测试重复调用（应被防护）
- [ ] 测试并发调用
- [ ] 检查日志确认状态

### 调试阶段
- [ ] 创建逐步测试脚本
- [ ] 对比简单测试和完整流程
- [ ] 检查日志中的重复操作
- [ ] 验证 UI 响应性

---

## 快速修复步骤

1. **添加状态标志**
   ```python
   self._operation_done = False
   ```

2. **添加防护检查**
   ```python
   if self._operation_done:
       return
   self._operation_done = True
   ```

3. **移除重复调用**
   ```python
   # 从多次调用改为单次
   QTimer.singleShot(500, self._operation)
   ```

4. **添加日志**
   ```python
   logger.info("Starting operation (first time)")
   logger.debug("Operation already done, skipping")
   ```

5. **测试验证**
   - 检查日志确认单次执行
   - 验证 UI 响应性
   - 测试重复调用被正确防护
