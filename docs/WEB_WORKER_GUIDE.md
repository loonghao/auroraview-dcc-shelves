# Web Worker 使用指南

## 概述

AuroraView 的 WebView2/WKWebView 后端原生支持 Web Workers,无需任何 Rust 端修改。Web Workers 允许你在前端 JavaScript 中运行多线程代码,适合处理计算密集型任务。

## 为什么使用 Web Workers?

### ✅ 适用场景

1. **数据处理**: 大量 JSON/CSV 数据解析
2. **复杂计算**: 图像处理、数学运算、加密解密
3. **后台任务**: 定期数据同步、日志处理
4. **避免 UI 冻结**: 将耗时操作移到后台线程

### ❌ 不适用场景

- **DOM 操作**: Workers 无法访问 DOM
- **简单任务**: 创建 Worker 有开销,简单任务不值得
- **需要同步结果**: Workers 是异步的

## 基础用法

### 1. 创建 Worker 文件

```javascript
// public/workers/data-processor.worker.js
self.addEventListener('message', (event) => {
  const { type, data } = event.data;
  
  switch (type) {
    case 'PROCESS_DATA':
      // 执行耗时计算
      const result = processLargeDataset(data);
      self.postMessage({ type: 'RESULT', result });
      break;
      
    case 'CANCEL':
      self.close(); // 终止 Worker
      break;
  }
});

function processLargeDataset(data) {
  // 模拟耗时操作
  const processed = data.map(item => {
    // 复杂计算...
    return item * 2;
  });
  return processed;
}
```

### 2. 在主线程使用 Worker

```javascript
// src/utils/worker-manager.js
class WorkerManager {
  constructor() {
    this.worker = null;
  }

  async processData(data) {
    return new Promise((resolve, reject) => {
      // 创建 Worker
      this.worker = new Worker('/workers/data-processor.worker.js');
      
      // 监听结果
      this.worker.onmessage = (event) => {
        if (event.data.type === 'RESULT') {
          resolve(event.data.result);
          this.worker.terminate(); // 清理
        }
      };
      
      // 监听错误
      this.worker.onerror = (error) => {
        reject(error);
        this.worker.terminate();
      };
      
      // 发送任务
      this.worker.postMessage({ type: 'PROCESS_DATA', data });
    });
  }

  cancel() {
    if (this.worker) {
      this.worker.postMessage({ type: 'CANCEL' });
      this.worker = null;
    }
  }
}

export default new WorkerManager();
```

### 3. React 集成示例

```jsx
import { useState } from 'react';
import workerManager from './utils/worker-manager';

function DataProcessor() {
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);

  const handleProcess = async () => {
    setProcessing(true);
    try {
      const data = Array.from({ length: 1000000 }, (_, i) => i);
      const processed = await workerManager.processData(data);
      setResult(processed);
    } catch (error) {
      console.error('Worker error:', error);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div>
      <button onClick={handleProcess} disabled={processing}>
        {processing ? 'Processing...' : 'Process Data'}
      </button>
      {result && <p>Processed {result.length} items</p>}
    </div>
  );
}
```

## 高级用法

### 1. 共享 Worker (Shared Workers)

适用于多个窗口/标签页共享同一个 Worker:

```javascript
// 创建共享 Worker
const sharedWorker = new SharedWorker('/workers/shared.worker.js');

// 通过 port 通信
sharedWorker.port.start();
sharedWorker.port.postMessage({ type: 'INIT' });
sharedWorker.port.onmessage = (event) => {
  console.log('Received:', event.data);
};
```

### 2. Worker 池 (Worker Pool)

管理多个 Worker 以提高并发性能:

```javascript
class WorkerPool {
  constructor(workerScript, poolSize = 4) {
    this.workers = Array.from(
      { length: poolSize },
      () => new Worker(workerScript)
    );
    this.taskQueue = [];
    this.availableWorkers = [...this.workers];
  }

  async execute(data) {
    return new Promise((resolve, reject) => {
      const task = { data, resolve, reject };
      
      if (this.availableWorkers.length > 0) {
        this.runTask(task);
      } else {
        this.taskQueue.push(task);
      }
    });
  }

  runTask(task) {
    const worker = this.availableWorkers.pop();
    
    worker.onmessage = (event) => {
      task.resolve(event.data);
      this.availableWorkers.push(worker);
      
      // 处理队列中的下一个任务
      if (this.taskQueue.length > 0) {
        this.runTask(this.taskQueue.shift());
      }
    };
    
    worker.onerror = (error) => {
      task.reject(error);
      this.availableWorkers.push(worker);
    };
    
    worker.postMessage(task.data);
  }

  terminate() {
    this.workers.forEach(w => w.terminate());
  }
}
```

## 最佳实践

### 1. 资源管理

```javascript
// ✅ 好的做法: 及时清理
const worker = new Worker('/worker.js');
worker.postMessage(data);
worker.onmessage = (e) => {
  console.log(e.data);
  worker.terminate(); // 完成后立即终止
};

// ❌ 坏的做法: 忘记清理
const worker = new Worker('/worker.js');
worker.postMessage(data);
// Worker 一直运行,浪费资源
```

### 2. 错误处理

```javascript
worker.onerror = (error) => {
  console.error('Worker error:', error.message);
  console.error('File:', error.filename);
  console.error('Line:', error.lineno);
  worker.terminate();
};
```

### 3. 数据传输优化

```javascript
// ✅ 使用 Transferable Objects (零拷贝)
const buffer = new ArrayBuffer(1024 * 1024); // 1MB
worker.postMessage({ buffer }, [buffer]); // 转移所有权

// ❌ 避免传输大对象 (会序列化/反序列化)
const hugeObject = { /* 大量数据 */ };
worker.postMessage(hugeObject); // 慢!
```

## 与 AuroraView Bridge 集成

```javascript
// 在 Worker 中无法直接使用 Bridge,需要通过主线程中转
// main.js
import { bridge } from 'auroraview-bridge';

const worker = new Worker('/worker.js');

worker.onmessage = async (event) => {
  if (event.data.type === 'CALL_PYTHON') {
    // Worker 请求调用 Python
    const result = await bridge.call('python_function', event.data.args);
    worker.postMessage({ type: 'PYTHON_RESULT', result });
  }
};

// worker.js
self.postMessage({
  type: 'CALL_PYTHON',
  args: { key: 'value' }
});
```

## 调试技巧

### Chrome DevTools

1. 打开 DevTools (F12)
2. 切换到 **Sources** 标签
3. 在左侧面板找到 **Workers** 节点
4. 点击 Worker 文件进行调试

### 日志输出

```javascript
// Worker 中的 console.log 会显示在主线程的 DevTools 中
self.addEventListener('message', (event) => {
  console.log('[Worker] Received:', event.data);
  // 处理...
});
```

## 性能对比

| 场景 | 主线程 | Web Worker | 性能提升 |
|------|--------|-----------|---------|
| 处理 100 万条数据 | 2000ms (UI 冻结) | 2000ms (UI 流畅) | ✅ 用户体验提升 |
| 图像处理 (1920x1080) | 500ms (UI 冻结) | 500ms (UI 流畅) | ✅ 用户体验提升 |
| JSON 解析 (10MB) | 300ms (UI 冻结) | 300ms (UI 流畅) | ✅ 用户体验提升 |

**注意**: Worker 本身不会让任务更快,但可以避免阻塞 UI 线程。

## 总结

- ✅ AuroraView 原生支持 Web Workers,无需配置
- ✅ 适合 CPU 密集型任务,避免 UI 冻结
- ✅ 使用 Worker Pool 提高并发性能
- ⚠️ 无法访问 DOM,需要通过 postMessage 通信
- ⚠️ 及时清理 Worker,避免内存泄漏

## 参考资源

- [MDN Web Workers API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API)
- [Using Web Workers](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Using_web_workers)
- [Transferable Objects](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Transferable_objects)

