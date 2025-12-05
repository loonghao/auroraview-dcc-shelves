# AuroraView DCC Shelves

[![PyPI version](https://img.shields.io/pypi/v/auroraview-dcc-shelves.svg)](https://pypi.org/project/auroraview-dcc-shelves/)
[![Python versions](https://img.shields.io/pypi/pyversions/auroraview-dcc-shelves.svg)](https://pypi.org/project/auroraview-dcc-shelves/)
[![License](https://img.shields.io/github/license/loonghao/auroraview-dcc-shelves.svg)](https://github.com/loonghao/auroraview-dcc-shelves/blob/main/LICENSE)
[![CI](https://github.com/loonghao/auroraview-dcc-shelves/actions/workflows/pr-checks.yml/badge.svg)](https://github.com/loonghao/auroraview-dcc-shelves/actions/workflows/pr-checks.yml)

[English](README.md)

一个动态的、基于 YAML 配置的 DCC（数字内容创作）软件工具架系统，由 [AuroraView](https://github.com/loonghao/auroraview) 框架驱动。

![DCC Shelves 预览](docs/images/preview.gif)

## ✨ 特性

- 🎨 **现代化 Web UI** - 使用 Vue 3 和 Tailwind CSS 构建的美观响应式界面
- 📝 **YAML 配置** - 通过简单的 YAML 文件定义工具和工具架
- 🔧 **多工具支持** - 启动 Python 脚本和外部可执行文件
- 🎯 **DCC 集成** - 支持 Maya、Houdini、Blender、Nuke 等软件
- 🔍 **搜索和过滤** - 通过实时搜索快速查找工具
- 🎛️ **可定制** - 将工具分组到工具架，添加图标和描述

## 📦 安装

```bash
pip install auroraview-dcc-shelves
```

如需 Qt 集成（DCC 软件必需）：

```bash
pip install auroraview-dcc-shelves[qt]
```

## 🚀 快速开始

### 1. 创建配置文件

创建 `shelf_config.yaml` 文件：

```yaml
shelves:
  - name: "建模"
    buttons:
      - name: "减面"
        icon: "layers"
        tool_type: "python"
        tool_path: "scripts/poly_reduce.py"
        description: "减少多边形数量"

      - name: "UV 展开"
        icon: "grid"
        tool_type: "python"
        tool_path: "scripts/uv_unwrap.py"
        description: "自动 UV 展开"

  - name: "工具"
    buttons:
      - name: "场景清理"
        icon: "folder"
        tool_type: "python"
        tool_path: "scripts/scene_cleaner.py"
        description: "清理未使用的节点"
```

### 2. 启动工具架

```python
from auroraview_dcc_shelves import ShelfApp, load_config

# 加载配置
config = load_config("shelf_config.yaml")

# 创建并显示工具架
app = ShelfApp(config)
app.show()
```

### 3. 在 Maya 中使用

```python
from auroraview_dcc_shelves import ShelfApp, load_config

config = load_config("/path/to/shelf_config.yaml")
app = ShelfApp(config, title="我的工具")
app.show(app="maya")  # 启用 DCC 集成
```

## 🔌 集成模式

AuroraView DCC Shelves 支持两种 DCC 应用集成模式：

### Qt 模式（默认）- 用于可停靠窗口

适用于：**Maya、Houdini、Nuke、3ds Max**

使用 `QtWebView` 进行原生 Qt 控件集成，支持 `QDockWidget` 停靠。

```python
from auroraview_dcc_shelves import ShelfApp, load_config

config = load_config("shelf_config.yaml")
app = ShelfApp(config)
app.show(app="maya", mode="qt")  # 默认模式
```

**特性：**
- ✅ 原生 Qt 控件 - 可停靠、嵌入布局
- ✅ 由 Qt 父子系统管理
- ✅ 父窗口关闭时自动清理
- ✅ 支持 QDockWidget 停靠

### HWND 模式 - 用于非 Qt 应用

适用于：**Unreal Engine，或 Qt 模式有问题时**

使用 `AuroraView` 的 HWND 进行独立窗口集成。

```python
from auroraview_dcc_shelves import ShelfApp, load_config

config = load_config("shelf_config.yaml")
app = ShelfApp(config)
app.show(app="maya", mode="hwnd")

# 获取 HWND 用于外部集成（如 Unreal Engine）
hwnd = app.get_hwnd()
if hwnd:
    print(f"窗口句柄: 0x{hwnd:x}")
```

**Unreal Engine 集成：**

```python
from auroraview_dcc_shelves import ShelfApp, load_config

config = load_config("shelf_config.yaml")
app = ShelfApp(config)
app.show(app="unreal", mode="hwnd")

# 嵌入到 Unreal 的 Slate UI
hwnd = app.get_hwnd()
if hwnd:
    import unreal
    unreal.parent_external_window_to_slate(hwnd)
```

**特性：**
- ✅ 独立窗口，可访问 HWND
- ✅ 可通过 HWND API 嵌入
- ✅ 适用于非 Qt 应用
- ⚠️ 非真正的 Qt 子控件（不支持 QDockWidget 停靠）

### 模式对比

| 特性 | Qt 模式 (`mode="qt"`) | HWND 模式 (`mode="hwnd"`) |
|------|----------------------|---------------------------|
| Qt 停靠 | ✅ 支持 | ❌ 不支持 |
| HWND 访问 | ⚠️ 有限 | ✅ 完全访问 |
| Unreal Engine | ❌ 不推荐 | ✅ 推荐 |
| Maya/Houdini/Nuke | ✅ 推荐 | ⚠️ 可用但无停靠 |
| 父子生命周期 | ✅ 自动 | ⚠️ 手动 |

## 📖 配置参考

### 按钮属性

| 属性 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `name` | string | ✅ | 工具显示名称 |
| `tool_type` | string | ✅ | `"python"` 或 `"executable"` |
| `tool_path` | string | ✅ | 脚本或可执行文件路径 |
| `icon` | string | ❌ | 图标名称（见可用图标） |
| `args` | list | ❌ | 命令行参数 |
| `description` | string | ❌ | 工具提示描述 |
| `id` | string | ❌ | 唯一标识符（自动生成） |

### 可用图标

`box`, `wrench`, `file-code`, `terminal`, `folder`, `image`, `film`, `music`, `palette`, `layers`, `cpu`, `database`, `globe`, `settings`, `zap`, `package`, `grid`, `pencil`

## 🎨 配色方案与视觉设计系统

AuroraView DCC Shelves 采用现代化深色主题，灵感来自 Apple 设计语言，为 DCC 艺术家打造专业沉浸式体验。

### 核心色板

| 颜色 | 十六进制 / 值 | 用途 |
|------|---------------|------|
| **深色背景** | `#0d0d0d` | 主背景、对话框 |
| **浅色背景** | `#1d1d1f` | 渐变顶部、悬浮表面 |
| **主要文字** | `#f5f5f7` | 主文字、标题 |
| **次要文字** | `rgba(255,255,255,0.6)` | 描述、标签 |
| **弱化文字** | `rgba(255,255,255,0.4)` | 非活动状态 |

### 品牌与强调色

| 颜色 | 十六进制 | 用途 |
|------|----------|------|
| **品牌色 400** | `#34d399` | 成功状态、活动指示器 |
| **品牌色 500** | `#10b981` | 主品牌色 |
| **品牌色 600** | `#059669` | 品牌悬停状态 |
| **强调色 400** | `#22d3ee` | 高亮、链接 |
| **强调色 500** | `#06b6d4` | 次要强调 |

### 状态颜色

| 状态 | 颜色 | 用途 |
|------|------|------|
| **信息** | `text-blue-400` | 信息提示 |
| **警告** | `text-amber-400` | 警告提醒 |
| **错误** | `text-red-400` | 错误状态 |
| **成功** | `text-emerald-400` | 成功确认 |
| **运行中** | `bg-orange-500` | 工具执行指示器 |

### UI 组件样式

#### 毛玻璃效果

```css
/* 主毛玻璃面板 */
.glass {
  background: rgba(28, 28, 30, 0.72);
  backdrop-filter: blur(20px) saturate(180%);
}

/* 次级毛玻璃面板 */
.glass-subtle {
  background: rgba(44, 44, 46, 0.6);
  backdrop-filter: blur(10px);
}
```

#### 工具按钮状态

| 状态 | 样式 |
|------|------|
| 默认 | `bg-white/[0.03]` 透明边框 |
| 悬停 | `bg-white/[0.08]` 配合 `border-white/10` |
| 按下 | `scale-95` 变换 |

#### 设计原则

1. **深色优先设计** - 针对 DCC 长时间工作优化
2. **微妙动画** - 基于弹簧的过渡效果，自然流畅
3. **极简界面** - 专注内容而非 UI 元素
4. **无障碍访问** - 清晰的对比度确保可读性

## 🛠️ 开发

### 环境设置

```bash
# 克隆仓库
git clone https://github.com/loonghao/auroraview-dcc-shelves.git
cd auroraview-dcc-shelves

# 安装依赖
uv sync --dev

# 安装前端依赖
npm install
```

### 运行测试

```bash
# 运行 Python 测试
uvx nox -s pytest

# 运行代码检查
uvx nox -s lint

# 格式化代码
uvx nox -s format
```

### 构建

```bash
# 构建前端
npm run build

# 构建 Python 包
uv build
```

## 📄 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE)。

## 🤝 贡献

欢迎贡献！请阅读我们的[贡献指南](CONTRIBUTING.md)了解详情。

## 🔗 相关项目

- [AuroraView](https://github.com/loonghao/auroraview) - 驱动本项目的 WebView 框架
- [AuroraView Maya Outliner](https://github.com/loonghao/auroraview-maya-outliner) - 另一个基于 AuroraView 的工具

## 📷 图片版权声明

本项目使用的 Banner 图片**仅用于演示目的**，**非商业用途**。

- 来源：[花瓣网](https://huaban.com/pins/4758761487)

如有侵权，请联系我们，我们将立即删除。
