# RFC 0001: 灵活配置系统与插件架构

> **状态**: 草案
> **作者**: AuroraView DCC Shelves 团队
> **创建日期**: 2026-01-07
> **目标版本**: v0.3.0

## 摘要

本 RFC 提出了一个灵活、可扩展的配置系统重构方案,旨在解决当前 YAML 配置系统的局限性,支持多 DCC (数字内容创作) 工具、多环境和多项目的复杂场景。新系统将引入插件架构,允许不同 DCC 工具扩展其配置能力,并提供层次化的配置管理、动态加载和运行时扩展能力。

## 主流方案调研

在设计本方案之前,我们调研了以下主流实现:

### 1. config-rs (rust-cli/config-rs)

**架构**: 基于 Builder 模式的分层配置系统,支持 12-factor 应用方法论。

**核心设计**:
```rust
use config::{Config, Environment, File};

let settings = Config::builder()
    // 1. 默认配置
    .add_source(File::with_name("config/default"))
    // 2. 环境特定配置 (dev/test/prod)
    .add_source(File::with_name(&format!("config/{}", env)).required(false))
    // 3. 环境变量覆盖
    .add_source(Environment::with_prefix("APP"))
    .build()?;
```

**关键特性**:
- **分层配置源**: 支持默认值、文件、环境变量等多层覆盖
- **格式支持**: TOML, JSON, YAML, INI, RON 等多种格式
- **深度合并**: 智能合并嵌套配置,而不是简单覆盖
- **路径访问**: 支持 JSONPath 风格的路径访问 (`redis.port`)
- **实时监控**: 支持监听配置文件变化并自动重载

**依赖库**:
- `serde` - 序列化/反序列化
- `toml`, `yaml`, `json` - 格式解析器

### 2. Starship (starship/starship)

**架构**: 基于配置文件 + 插件模块的提示符定制系统。

**核心设计**:
```toml
# ~/.config/starship.toml
format = "$all"

[character]
success_symbol = "[➜](bold green)"
error_symbol = "[➜](bold red)"

[directory]
truncation_length = 3
truncate_to_repo = true

# 模块化配置
[custom.python]
when = """ test -f requirements.txt || test -f pyproject.toml """
symbol = "🐍 "
style = "bold yellow"
format = "via [$symbol]($style) "
```

**关键特性**:
- **模块化设计**: 每个功能模块独立配置
- **条件加载**: 支持基于条件的模块激活
- **深度自定义**: 每个模块支持丰富的样式配置
- **多语言支持**: 内置国际化字段 (`name_zh`)

**设计启示**:
- 配置文件应该清晰易读,支持注释
- 模块化设计让用户可以只关心自己使用的部分
- 条件加载机制可以根据运行时环境动态调整配置

### 3. Maya/Houdini Plugin Configuration

**架构**: 基于 JSON/XML 文件的插件系统,每个插件独立声明其能力和配置。

**核心设计**:
```python
# Maya plugin.py
def maya_useNewAPI():
    return True

def maya_getPluginName():
    return "MyPlugin"

def initializePlugin(mobject):
    mplugin = MFnPlugin(mobject)
    mplugin.registerCommand("myCommand", MyCommand())
    mplugin.registerFileTranslator("MyFormat", None, MyTranslator)
```

**关键特性**:
- **自描述**: 插件自己声明其类型和能力
- **动态加载**: 运行时动态加载和卸载插件
- **版本控制**: 支持插件版本检测
- **隔离性**: 插件之间相互独立,不会相互影响

**设计启示**:
- 插件应该能够自描述其能力和依赖
- 配置系统需要支持插件的动态发现和加载
- 版本管理机制很重要,特别是跨 DCC 兼容性

### 方案对比

| 特性 | config-rs | Starship | AuroraView 当前 | 本 RFC 方案 |
|------|-----------|----------|----------------|-------------|
| 分层配置 | ✓ 深度合并 | ✓ 模块化 | ✓ 简单引用 | ✓ 深度合并 + 模块化 |
| 多格式支持 | ✓ TOML/YAML/JSON | ✗ TOML | ✓ YAML | ✓ YAML + 插件格式 |
| 插件系统 | ✗ | ✓ 自定义模块 | ✗ | ✓ DCC 插件 + 扩展插件 |
| 环境感知 | ✓ 环境变量 | ✓ 条件加载 | ✓ hosts 字段 | ✓ 智能环境感知 |
| 运行时扩展 | ✓ 文件监控 | ✗ | ✗ | ✓ 热重载 + 动态插件 |
| 国际化 | ✗ | ✓ _zh 字段 | ✓ _zh 字段 | ✓ 多语言 + 插件翻译 |
| 配置验证 | ✓ serde | ✗ | ✓ 基础验证 | ✓ Schema + 自定义验证 |

### 设计启示

基于以上调研,本 RFC 应采用:

1. **分层配置架构** - 采用 config-rs 的分层设计,支持默认值 → DCC 配置 → 环境配置 → 环境变量 → 命令行参数的优先级
2. **模块化设计** - 参考 Starship 的模块化思想,将配置按 DCC、项目、环境等维度组织
3. **插件系统** - 结合 Maya/Houdini 的插件设计,允许第三方扩展配置能力
4. **Schema 验证** - 引入配置 Schema,在加载时验证配置的正确性
5. **热重载机制** - 支持配置文件变化时自动重载,无需重启应用

## 动机

### 当前状态分析

当前 `auroraview-dcc-shelves` 项目使用单一的 YAML 配置文件系统,具有以下特点:

**现有功能**:
- ✅ 基础 YAML 配置解析
- ✅ 通过 `ref` 字段引用外部文件实现模块化
- ✅ 支持国际化字段 (`name_zh`, `description_zh`)
- ✅ 基于 hosts 字段的 DCC 过滤
- ✅ 循环引用检测
- ✅ 路径自动调整

**当前局限**:
- ❌ **单层配置**: 没有真正的分层配置能力,无法处理"默认配置 → 项目配置 → 个人配置"的场景
- ❌ **环境隔离不足**: 虽然有 hosts 字段,但无法区分开发/测试/生产环境
- ❌ **配置臃肿**: 单个文件包含所有 DCC 的配置,导致文件过大难以维护
- ❌ **缺乏插件机制**: 无法通过插件扩展配置系统本身的能力
- ❌ **类型安全弱**: 配置加载后才发现错误,没有加载前的验证
- ❌ **无法热重载**: 修改配置需要重启应用才能生效
- ❌ **DCC 特定配置受限**: 无法为不同 DCC 提供特定于该 DCC 的配置选项

### 需求分析

基于项目发展和用户反馈,我们识别出以下核心需求:

1. **多环境支持**
   - 开发环境 (dev): 启用调试工具,详细日志
   - 测试环境 (test): 连接测试服务器,模拟数据
   - 生产环境 (prod): 优化性能,关闭调试功能

2. **多项目支持**
   - 不同项目有不同的工具需求
   - 项目可以有自己的工具配置
   - 支持项目模板和继承

3. **DCC 特定配置**
   - Maya 需要 Python API 配置、MEL 脚本路径
   - Houdini 需要 HDA 路径、OTL 配置
   - Blender 需要 Add-on 配置、Python 路径

4. **插件扩展能力**
   - 第三方可以开发 DCC 插件
   - 插件可以注册自己的配置 Schema
   - 插件可以提供自定义验证器

5. **配置验证**
   - 加载前验证配置格式
   - Schema 驱动的类型检查
   - 自定义验证规则

6. **动态更新**
   - 配置文件变化时自动重载
   - 无需重启应用
   - 提供配置变更事件

7. **优先级管理**
   - 清晰的配置优先级规则
   - 支持覆盖和合并策略
   - 可以查看最终配置的来源

## 设计方案

### 完整配置/API 预览

```yaml
# auroraview_config.yaml - 主配置文件

version: "2.0"
config_schema: "auroraview://schemas/v2"

# 配置优先级 (从低到高):
# 1. 默认配置 (defaults.yaml)
# 2. DCC 特定配置 (dcc/maya.yaml, dcc/houdini.yaml)
# 3. 环境配置 (environments/dev.yaml)
# 4. 项目配置 (projects/my_project.yaml)
# 5. 用户配置 (~/.auroraview/user.yaml)
# 6. 环境变量 (AURORAVIEW_*)
# 7. 命令行参数

# 环境定义
environments:
  dev:
    debug: true
    log_level: "DEBUG"
    hot_reload: true

  test:
    debug: false
    log_level: "INFO"
    test_data_path: "./test/data"

  production:
    debug: false
    log_level: "WARNING"
    performance_mode: true

# DCC 配置
dcc_config:
  maya:
    version: "2022-2024"
    python_path:
      - "$MAYA_LOCATION/python/lib/python3.10/site-packages"
    mel_path:
      - "$AURORAVIEW_ROOT/scripts/maya"
    auto_load_plugins:
      - "mayaUsd"
      - "mtoa"

  houdini:
    version: "19.5-20.5"
    otl_path:
      - "$AURORAVIEW_ROOT/hdas"
    dso_path:
      - "$AURORAVIEW_ROOT/dsos"
    environment_variables:
      HOUDINI_OTLSCAN_PATH: "$HOUDINI_OTLSCAN_PATH;$AURORAVIEW_ROOT/hdas"

  blender:
    version: "3.6-4.2"
    addons:
      - name: "io_import_scene"
        enabled: true
      - name: "mesh_tools"
        enabled: false

# 项目配置模板
projects:
  default:
    # 默认项目配置
    asset_root: "${PROJECT_ROOT}/assets"
    shot_root: "${PROJECT_ROOT}/shots"

  "my_vfx_project":
    # 特定项目配置
    extends: "default"
    asset_root: "/studio/projects/vfx/assets"
    custom_tools:
      - ref: "./tools/vfx_pipeline.yaml"

# 工具架配置
shelves:
  # 通用工具
  - name: Universal
    priority: 0
    environment: ["dev", "test", "production"]
    buttons:
      - name: Hello World
        tool_type: python
        tool_path: scripts/hello_world.py
        description: Simple hello world
        name_zh: 你好世界
        description_zh: 简单的 hello world 消息
        # 元数据
        version: "1.2.0"
        maintainer: "Pipeline Team"
        tags: ["demo", "basic"]
        # 环境特定配置
        environments:
          dev:
            hot_reload: true
          production:
            validation: strict

  # Maya 特定工具
  - name: Maya Tools
    priority: 10
    dcc: ["maya"]
    environments: ["dev", "test", "production"]
    # 引用外部配置文件
    ref: "./dcc/maya/tools.yaml"

# 插件配置
plugins:
  - name: "asset_browser"
    enabled: true
    version: "4.0.0"
    config:
      thumbnail_size: 256
      cache_enabled: true
    environments: ["dev", "production"]

  - name: "render_farm_integration"
    enabled: false
    config:
      farm_url: "https://renderfarm.studio.com/api"
    environments: ["production"]

# UI 配置
ui:
  theme: "dark"
  language: "auto"  # auto, en, zh
  window:
    width: 1200
    height: 800
    dockable: true

# 调试配置
debug:
  show_config_sources: true  # 显示每个配置项的来源
  log_config_changes: true   # 记录配置变化
```

### 详细说明

#### 1. 配置层次结构

新系统采用六层配置架构,从低优先级到高优先级:

```
Level 1: 默认配置
  ├─ config/defaults.yaml
  └─ 包含所有默认值和基础配置

Level 2: DCC 特定配置
  ├─ config/dcc/maya.yaml
  ├─ config/dcc/houdini.yaml
  ├─ config/dcc/blender.yaml
  └─ 包含特定 DCC 的配置和工具

Level 3: 环境配置
  ├─ config/environments/dev.yaml
  ├─ config/environments/test.yaml
  └─ config/environments/production.yaml

Level 4: 项目配置
  ├─ config/projects/default.yaml
  ├─ config/projects/my_project.yaml
  └─ 每个项目可以有自己的配置

Level 5: 用户配置
  └─ ~/.auroraview/config.yaml
      └─ 用户个人配置,覆盖项目配置

Level 6: 运行时配置
  ├─ 环境变量 (AURORAVIEW_*)
  └─ 命令行参数 (--config, --debug, etc.)
```

**合并策略**:
- **简单值**: 后面的层级覆盖前面的
- **列表**: 合并去重 (基于 ID 或 name)
- **字典**: 深度合并
- **特殊字段**:
  - `extends`: 继承另一个配置
  - `ref`: 引用外部文件
  - `environment`: 环境特定配置

#### 2. 配置加载 API

```python
from auroraview_dcc_shelves.config import ConfigLoader, Config

# 创建配置加载器
loader = ConfigLoader()

# 设置当前环境
loader.set_environment("dev")

# 加载主配置文件
config: Config = loader.load("auroraview_config.yaml")

# 访问配置
print(config.dcc.maya.version)  # "2022-2024"
print(config.ui.theme)           # "dark"

# 获取特定 DCC 的工具架
maya_shelves = config.get_shelves_for_dcc("maya")

# 获取环境特定配置
dev_config = config.get_environment_config("dev")

# 查看配置来源
source = config.get_source("ui.theme")  # "config/environments/dev.yaml"

# 监听配置变化
@config.on_change
def on_config_changed(changed_keys):
    print(f"Configuration changed: {changed_keys}")

# 手动重载配置
config.reload()
```

#### 3. 插件系统设计

插件系统允许第三方扩展配置系统的能力:

**插件接口**:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class ConfigPlugin(ABC):
    """配置插件基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """插件版本"""
        pass

    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """返回插件的配置 Schema"""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, list[str]]:
        """验证配置

        Returns:
            (is_valid, error_messages)
        """
        pass

    @abstractmethod
    def transform_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换配置 (可选)"""
        return config

    def on_config_loaded(self, config: 'Config'):
        """配置加载后的回调"""
        pass
```

**插件示例**:

```python
class AssetBrowserPlugin(ConfigPlugin):
    """资产浏览器插件"""

    @property
    def name(self) -> str:
        return "asset_browser"

    @property
    def version(self) -> str:
        return "4.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "thumbnail_size": {"type": "integer", "minimum": 64, "maximum": 1024},
                "cache_enabled": {"type": "boolean"},
                "cache_ttl": {"type": "integer", "minimum": 60},
                "supported_formats": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["thumbnail_size", "cache_enabled"]
        }

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, list[str]]:
        errors = []
        if config.get("thumbnail_size", 0) > 1024:
            errors.append("thumbnail_size cannot exceed 1024")
        return len(errors) == 0, errors

    def transform_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # 设置默认值
        config.setdefault("cache_ttl", 3600)
        config.setdefault("supported_formats", ["usd", "abc", "fbx"])
        return config

    def on_config_loaded(self, config: 'Config'):
        print(f"Asset Browser plugin loaded with config: {config.plugins.asset_browser}")

# 注册插件
loader = ConfigLoader()
loader.register_plugin(AssetBrowserPlugin())
```

#### 4. 配置 Schema 验证

使用 JSON Schema 进行配置验证:

```python
import jsonschema

# 定义 Schema
CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
        "environments": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "debug": {"type": "boolean"},
                    "log_level": {"enum": ["DEBUG", "INFO", "WARNING", "ERROR"]}
                }
            }
        },
        "shelves": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "buttons": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "tool_type", "tool_path"],
                            "properties": {
                                "tool_type": {"enum": ["python", "executable", "mel", "javascript"]}
                            }
                        }
                    }
                }
            }
        }
    }
}

# 验证配置
loader = ConfigLoader(config_schema=CONFIG_SCHEMA)
try:
    config = loader.load("auroraview_config.yaml")
except ValidationError as e:
    print(f"Configuration validation error: {e}")
```

#### 5. 热重载机制

使用文件监控器实现配置热重载:

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigFileHandler(FileSystemEventHandler):
    def __init__(self, config: 'Config'):
        self.config = config

    def on_modified(self, event):
        if event.src_path.endswith('.yaml'):
            print(f"Config file changed: {event.src_path}")
            self.config.reload()

# 启动监控
observer = Observer()
observer.schedule(ConfigFileHandler(config), path="config/", recursive=True)
observer.start()

# 修改配置文件后自动重载,无需重启应用
```

#### 6. 配置调试工具

提供工具帮助调试配置:

```python
# 查看配置树
config.dump_tree()

# 查看特定配置项
config.dump("dcc.maya")

# 查看配置来源
config.dump_sources()

# 验证配置
warnings = config.validate()
for warning in warnings:
    print(f"Warning: {warning}")

# 导出当前配置
config.export("current_config.yaml")

# 比较两个配置
diff = Config.compare("config_a.yaml", "config_b.yaml")
print(diff)
```

## 向后兼容性

### 兼容策略

1. **版本检测**
   - 配置文件包含 `version` 字段
   - v1.0 格式自动迁移到 v2.0
   - v2.0 格式完全使用新系统

2. **渐进增强**
   - 所有新字段都是可选的
   - 旧配置文件可以正常加载
   - 新功能默认关闭

3. **默认值**
   - 为所有新字段提供合理的默认值
   - 不破坏现有配置的行为

4. **警告处理**
   - 遇到未知字段时警告但不报错
   - 提供迁移工具帮助用户升级

### 迁移路径

```bash
# 检查配置兼容性
auroraview-config check shelf_config.yaml

# 自动迁移到 v2.0
auroraview-config migrate --to v2 shelf_config.yaml

# 验证迁移后的配置
auroraview-config validate shelf_config.yaml

# 查看迁移差异
auroraview-config diff shelf_config.yaml shelf_config_v2.yaml
```

**迁移工具实现**:

```python
class ConfigMigrator:
    """配置迁移工具"""

    def migrate_v1_to_v2(self, old_config: dict) -> dict:
        """将 v1.0 配置迁移到 v2.0"""
        new_config = {
            "version": "2.0",
            "environments": {
                "production": {}  # 默认环境
            },
            "shelves": [],
            "plugins": []
        }

        # 迁移 banner
        if "banner" in old_config:
            new_config["ui"] = {
                "title": old_config["banner"].get("title", "Toolbox"),
                "title_zh": old_config["banner"].get("title_zh", ""),
                "theme": "dark"
            }

        # 迁移 shelves
        for shelf in old_config.get("shelves", []):
            new_shelf = {
                "name": shelf["name"],
                "name_zh": shelf.get("name_zh", ""),
                "environment": ["production"],  # 默认环境
                "buttons": shelf.get("buttons", [])
            }
            new_config["shelves"].append(new_shelf)

        return new_config
```

## 实现计划

### Phase 1: Core Features (v0.3.0)

- [ ] 实现分层配置加载器
- [ ] 实现配置合并策略
- [ ] 实现基础插件系统
- [ ] 实现 JSON Schema 验证
- [ ] 编写迁移工具
- [ ] 文档和示例

### Phase 2: Extended Features (v0.4.0)

- [ ] 实现热重载机制
- [ ] 实现配置调试工具
- [ ] 实现配置缓存
- [ ] 实现国际化增强
- [ ] 编写插件开发文档

### Phase 3: Advanced Features (v0.5.0)

- [ ] 实现配置 GUI 编辑器
- [ ] 实现配置版本管理
- [ ] 实现配置远程同步
- [ ] 实现性能优化
- [ ] 完整测试覆盖

## 替代方案

### 方案 A: 保持现有 YAML + 添加环境变量

**优点**:
- 改动最小
- 实现简单

**缺点**:
- 不支持真正的分层配置
- 无法支持复杂的插件系统
- 扩展性有限

**结论**: 不采用,无法满足长期需求

### 方案 B: 完全迁移到 Python 配置

**优点**:
- 类型安全
- 支持任意 Python 代码

**缺点**:
- 不适合版本控制
- 配置和代码混在一起
- 用户需要懂 Python

**结论**: 不采用,YAML 更适合配置场景

### 方案 C: 使用 TOML 替代 YAML

**优点**:
- TOML 语法更简洁
- 更好的性能

**缺点**:
- YAML 已被现有配置使用
- TOML 对复杂结构的支持不如 YAML
- 迁移成本高

**结论**: 不采用,保留 YAML 格式

## 参考资料

### 主流项目源码
- [config-rs 源码](https://github.com/rust-cli/config-rs) - 分层配置系统的主要参考
- [Starship 源码](https://github.com/starship/starship) - 模块化配置和插件系统的参考
- [Maya 插件 API](https://help.autodesk.com/view/MAYAUL/2024/ENU/) - 插件设计和配置管理的参考

### 依赖库
- [PyYAML](https://pyyaml.org/) - YAML 解析
- [jsonschema](https://github.com/python-jsonschema/jsonschema) - Schema 验证
- [watchdog](https://python-watchdog.readthedocs.io/) - 文件监控和热重载

### 相关文档
- [AuroraView DCC Shelves README](https://github.com/loonghao/auroraview-dcc-shelves)
- [12-Factor App](https://12factor.net/config) - 配置管理最佳实践
- [JSON Schema 规范](https://json-schema.org/) - Schema 定义标准

## 更新记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-01-07 | Draft | 初始草案 |
