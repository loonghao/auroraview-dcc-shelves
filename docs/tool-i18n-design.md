# Tool Translation (工具翻译) 设计方案

## 概述

工具数据来自 YAML 配置文件，包含 `name`、`description`、`category` 等需要翻译的字段。本方案采用**离线优先 + 自动生成**的混合策略。

## 推荐方案：YAML 多语言扩展 + 自动生成脚本

### 1. YAML 配置格式扩展

```yaml
# shelf_config.yaml - 支持多语言
shelves:
  - name: "Modeling"
    name_zh: "建模"  # 中文名称
    buttons:
      - name: "Poly Reduce"
        name_zh: "多边形精简"
        description: "Reduce polygon count while preserving shape"
        description_zh: "在保持形状的同时减少多边形数量"
        icon: "Layers"
        tool_type: "python"
        tool_path: "scripts/poly_reduce.py"
```

### 2. 自动翻译生成脚本

使用免费的翻译 API 批量生成翻译：

| 服务 | 免费额度 | 特点 |
|------|----------|------|
| **LibreTranslate** | 无限（自托管） | 开源、离线可用 |
| **MyMemory** | 1000次/天 | 无需注册 |
| **Lingva** | 无限 | Google Translate 代理 |

### 3. 前端加载逻辑

```typescript
// 根据当前语言选择显示文本
const getLocalizedName = (tool: ButtonConfig, lang: string): string => {
  if (lang === 'zh' && tool.name_zh) return tool.name_zh
  return tool.name // 回退到默认语言
}
```

## 实现步骤

### Step 1: 创建翻译脚本

```bash
scripts/
├── translate_tools.py    # 自动翻译生成器
└── translation_cache.json # 翻译缓存
```

### Step 2: 扩展类型定义

```typescript
// types.ts
interface ButtonConfig {
  name: string
  name_zh?: string  // 中文名
  description: string
  description_zh?: string
}
```

### Step 3: 前端本地化 Hook

```typescript
// hooks/useLocalizedTool.ts
export function useLocalizedTool(tool: ButtonConfig) {
  const { i18n } = useTranslation()
  const lang = i18n.language.split('-')[0]

  return {
    name: tool[`name_${lang}`] || tool.name,
    description: tool[`description_${lang}`] || tool.description,
  }
}
```

## 自动翻译脚本示例

```python
# scripts/translate_tools.py
"""Auto-translate tool names and descriptions using free APIs."""

import json
import requests
from pathlib import Path
import yaml

CACHE_FILE = Path("scripts/translation_cache.json")
LINGVA_API = "https://lingva.ml/api/v1/en/zh"

def translate_text(text: str) -> str:
    """Translate English to Chinese using Lingva (free Google Translate proxy)."""
    # Check cache first
    cache = load_cache()
    if text in cache:
        return cache[text]

    # Call API
    response = requests.get(f"{LINGVA_API}/{text}")
    if response.ok:
        translation = response.json().get("translation", text)
        # Save to cache
        cache[text] = translation
        save_cache(cache)
        return translation
    return text

def translate_yaml_config(config_path: str) -> None:
    """Add translations to YAML config file."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    for shelf in config.get("shelves", []):
        # Translate shelf name
        if "name_zh" not in shelf:
            shelf["name_zh"] = translate_text(shelf["name"])

        # Translate buttons
        for button in shelf.get("buttons", []):
            if "name_zh" not in button:
                button["name_zh"] = translate_text(button["name"])
            if "description_zh" not in button and button.get("description"):
                button["description_zh"] = translate_text(button["description"])

    # Save updated config
    with open(config_path, "w") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)
```

## 运行流程

```bash
# 1. 自动翻译 YAML 配置
just translate-tools

# 2. 构建前端
npm run build

# 3. 运行应用（翻译已嵌入配置）
just run
```

## 优势

1. **离线优先** - 翻译嵌入 YAML，无需运行时 API
2. **免费方案** - 使用开源翻译 API
3. **缓存机制** - 避免重复翻译
4. **可编辑** - 人工可修正自动翻译
5. **向后兼容** - 缺少翻译时回退到英文

## 下一步

1. [ ] 实现 `translate_tools.py` 脚本
2. [ ] 扩展 `ButtonConfig` 类型
3. [ ] 创建 `useLocalizedTool` Hook
4. [ ] 更新 YAML 配置格式
5. [ ] 添加 justfile 命令
