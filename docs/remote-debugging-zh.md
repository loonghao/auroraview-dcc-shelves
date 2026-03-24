# 通过 Chrome DevTools Protocol (CDP) 进行远程调试

## 概述

AuroraView DCC Shelves 通过 `remote_debugging_port` 参数支持 Chrome DevTools Protocol (CDP)。这提供了强大的自动化和调试功能，允许 MCP、Playwright 和 Puppeteer 等工具控制 WebView。

## 快速开始

### 在 DCC 模式中启用远程调试

```python
from auroraview_dcc_shelves import ShelfApp, load_config

config = load_config("shelf_config.yaml")
app = ShelfApp(config, remote_debugging_port=9222)
app.show(app="maya", mode="qt")

# 可以通过以下方式连接：
# - chrome://inspect
# - MCP (http://127.0.0.1:9222 或 ws://127.0.0.1:9222)
# - Playwright
# - Puppeteer
```

### 在桌面模式中启用远程调试

```python
from auroraview_dcc_shelves.apps.desktop import run_desktop

run_desktop(
    config_path="shelf_config.yaml",
    debug=True,
    remote_debugging_port=9222
)
```

## 连接到 WebView

一旦启用了 `remote_debugging_port` 的 WebView 运行起来，你可以使用各种工具连接：

### Chrome DevTools

1. 打开 Chrome/Edge 浏览器
2. 导航到 `chrome://inspect`
3. 点击 "Configure..." 并添加 `localhost:9222`
4. WebView 将出现在 "Remote Target" 下
5. 点击 "inspect" 打开 DevTools

### MCP (Model Context Protocol)

连接你的 AI 助手来控制 WebView：

```json
{
  "mcpServers": {
    "dcc-shelves": {
      "command": "npx",
      "args": ["@anthropic-ai/mcp-server-puppeteer"],
      "env": {
        "CDP_URL": "http://127.0.0.1:9222"
      }
    }
  }
}
```

### Playwright

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    context = browser.contexts[0]
    page = context.pages[0]

    # 自动化 WebView
    page.click('[data-testid="tool-button"]')
```

### Puppeteer

```javascript
const puppeteer = require('puppeteer-core');

(async () => {
    const browser = await puppeteer.connect({
        browserURL: 'http://127.0.0.1:9222'
    });

    const pages = await browser.pages();
    const page = pages[0];

    // 自动化 WebView
    await page.click('[data-testid="tool-button"]');
})();
```

## 使用场景

### 1. UI 自动化测试

```python
# pytest 测试文件
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture
def shelf_app():
    """启动带远程调试的 ShelfApp。"""
    from auroraview_dcc_shelves import ShelfApp, load_config

    config = load_config("shelf_config.yaml")
    app = ShelfApp(config, remote_debugging_port=9222)
    app.show(app="maya", mode="qt")
    yield app
    app.close()

def test_tool_launch(shelf_app):
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = browser.contexts[0].pages[0]

        # 点击工具按钮
        page.click('text="Poly Reduce"')

        # 验证工具已启动
        assert page.locator('.toast-success').is_visible()
```

### 2. AI 辅助工作流

让 AI 工具与你的 DCC 工具架交互：

```python
# 在你的 DCC 启动脚本中
from auroraview_dcc_shelves import ShelfApp, load_config

config = load_config("shelf_config.yaml")
app = ShelfApp(
    config,
    remote_debugging_port=9222  # 启用 MCP 控制
)
app.show(app="maya", mode="qt")

print("CDP 已就绪: http://127.0.0.1:9222")
print("AI 助手现在可以控制工具架了！")
```

### 3. 远程调试生产问题

```python
# 临时启用调试以排查问题
from auroraview_dcc_shelves import ShelfApp, load_config
import os

# 仅在设置了 SHELF_DEBUG 时启用
debug_port = int(os.environ.get("SHELF_DEBUG_PORT", 0)) or None

config = load_config("shelf_config.yaml")
app = ShelfApp(config, remote_debugging_port=debug_port)
app.show(app="maya", mode="qt")
```

## API 参考

### ShelfApp 参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `remote_debugging_port` | `int \| None` | `None` | CDP 端口。设置后启用远程调试。 |

### ShelfApp 属性

| 属性 | 类型 | 描述 |
|------|------|------|
| `remote_debugging_port` | `int \| None` | 获取配置的 CDP 端口。 |

## 常用端口

| 端口 | 用途 |
|------|------|
| 9222 | Chrome DevTools 默认端口 |
| 9223 | 多实例时的替代端口 |
| 9333 | 另一个常用替代端口 |

## 安全注意事项

⚠️ **重要**：远程调试会暴露对 WebView 的完全控制权。请考虑以下安全实践：

1. **仅在本地使用** - 默认绑定是 `127.0.0.1`
2. **在生产环境中关闭端口** - 仅在需要时启用
3. **使用防火墙规则** - 阻止对调试端口的外部访问
4. **不要暴露敏感数据** - 请注意所有页面内容都可以被访问

## 故障排除

### 端口已被占用

```python
# 使用不同的端口
app = ShelfApp(config, remote_debugging_port=9333)
```

### 连接被拒绝

1. 确保 ShelfApp 正在运行且 WebView 已初始化
2. 检查端口是否正确
3. 验证防火墙没有阻止连接

### DevTools 显示空白页

1. 等待 WebView 完全加载
2. 刷新 DevTools 连接
3. 检查控制台是否有 JavaScript 错误
