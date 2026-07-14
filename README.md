<div align="center">

<img src="screenshot.png" alt="ImgBatch" width="600" />

# ImgBatch v2.0

### 全能图片批处理工具箱 · All-in-One Batch Image Toolkit

压缩 · 格式转换 · 批量重命名 · 水印 · AI 智能重命名 · 裁剪透明 · 规范化 · 检查
*Compress · Convert · Rename · Watermark · AI Rename · Trim · Normalize · Inspect*

[![Python](https://img.shields.io/badge/Python-3.7+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Pillow](https://img.shields.io/badge/Pillow-9.0+-darkgreen)](https://python-pillow.org)
[![DeepSeek](https://img.shields.io/badge/AI-DeepSeek-4D6BFE)](https://deepseek.com)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)]()
[![Tests](https://img.shields.io/badge/Tests-pytest-success)](tests/)

</div>

---

## 🆕 v2.0 新特性 · What's New

| 特性 | 说明 |
|:---|:---|
| 🏗️ **模块化架构** | 业务逻辑与 UI 完全分离，核心层无 GUI 依赖，可独立测试 |
| 💾 **设置持久化** | 所有参数自动保存到 `~/.imgbatch/config.json`，重启不丢失 |
| 📝 **结构化日志** | 所有操作和错误记录到 `~/.imgbatch/imgbatch.log` |
| 🧪 **单元测试** | 核心逻辑 100% 测试覆盖，pytest 测试套件 |
| 🔒 **线程安全** | 取消机制 + ThreadPoolExecutor + try/finally 保证状态一致性 |
| ↩️ **操作撤销** | Ctrl+Z 撤销上次操作，支持重命名和备份恢复 |
| 🌐 **i18n 完整化** | 所有 UI 文本通过翻译系统，语言切换不再丢失状态 |
| ⚡ **CLI 接口** | 无 GUI 批量处理，支持自动化脚本和 CI/CD |
| 🤖 **Agent Skill** | 内置 AI agent skill，可被编程助手调用 |
| 🔄 **递归扫描** | 支持子目录递归扫描图片 |
| 📊 **ETA 估算** | 实时显示预计剩余时间 |
| 📋 **EXIF 控制** | 保留 / 清除 / 仅方向 三种 EXIF 处理模式 |
| 🛡️ **冲突检测** | 重命名时自动检测文件名冲突，支持跳过/覆盖/自动序号 |
| 🎯 **多格式预估** | 压缩预览按格式分组采样，多格式混合预估更准确 |
| 🔁 **AI 加固** | DeepSeek API 3 次指数退避重试 + 响应验证 + 分批发送 + token 追踪 |

---

## ✨ 八大核心功能 · Eight Core Modules

<table>
<tr>
<td width="50%">

### 🗜️ 压缩 Compress
- 质量 1%–100% 无级调节
- 缩放比例 10%–100%
- EXIF 保留 / 清除 / 仅方向
- 替换原文件 / 输出新文件夹
- 自动备份 + 备份管理（恢复/清除）
- 实时大小预估（多格式分组采样）
- 支持同步格式转换 / 重命名 / 水印

### 🔄 格式转换 Format
- JPG ⇄ PNG ⇄ WEBP ⇄ BMP ⇄ TIFF ⇄ GIF ⇄ ICO
- 智能透明度处理（RGBA→RGB）
- 可替换原文件或输出到新目录

### 🏷️ 批量重命名 Rename
- 添加前缀 / 后缀
- 查找替换文本
- 序号模板 `photo_{num}`（自定义位数+起始值）
- 全大写 / 全小写转换
- **冲突检测**（跳过/覆盖/自动加序号）
- 实时预览

### 💧 水印 Watermark
- 文字水印：内容、字号、颜色(#HEX)、透明度
- 图片水印：PNG LOGO、缩放比例、透明度
- 位置：左上/右上/居中/左下/右下
- 支持备份和双输出模式

</td>
<td width="50%">

### 🤖 AI 智能重命名 AI Rename
- 接入 **DeepSeek** API
- 自定义提示词
- 预览 AI 建议 → 一键应用
- **3 次指数退避重试**
- **响应结构验证**
- **分批发送**（每批最多 100 个文件名）
- **Token 用量追踪**
- 本地调用，不上传服务器

### ✂️ 裁剪透明 Trim Alpha
- 裁剪 PNG 透明边距
- 自定义边距 padding
- 支持备份和双输出模式

### 🔍 检查 Inspect
- 检查 PNG 画布尺寸 / 内容尺寸
- 上下左右边距分析
- 批量结果表格展示

### 📐 规范化 Normalize
- Alpha 阈值裁剪
- 统一目标高度缩放
- 均匀透明边距
- 适用于标题图片统一规格

</td>
</tr>
</table>

---

## 🚀 快速开始 Quick Start

### GUI 模式

```bash
# 安装依赖
pip install Pillow

# 运行 GUI
python image_compressor.pyw
```

> 双击 `启动.bat` 一键启动

### CLI 模式

```bash
# 压缩
python -m imgbatch.cli compress -f ./photos --quality 75 --resize 50

# 格式转换
python -m imgbatch.cli convert -f ./photos --to webp

# 批量重命名
python -m imgbatch.cli rename -f ./photos --mode seq --template "photo_{num}" --start 1

# 水印
python -m imgbatch.cli watermark -f ./photos --text "© 2026" --opacity 50

# 裁剪透明边距
python -m imgbatch.cli trim -f ./pngs --padding 4

# 规范化
python -m imgbatch.cli normalize -f ./pngs --target-height 280

# 检查 PNG
python -m imgbatch.cli inspect -f ./pngs

# AI 重命名
python -m imgbatch.cli ai-rename -f ./photos --api-key sk-xxx --apply
```

### 运行测试

```bash
pip install pytest
pytest tests/ -v
```

### 📦 打包为 EXE Build to EXE

```bash
# 一键打包（自动检测 imgbatch 包所有子模块）
build.bat

# 或手动执行
pip install pyinstaller
python build.py
```

> 输出文件在 `dist/ImgBatch.exe`，单文件便携，无需安装 Python

---

## 🔑 AI 重命名配置

1. 获取 [DeepSeek API Key](https://platform.deepseek.com/api_keys)
2. 粘贴到「AI重命名」标签页
3. 可自定义提示词（默认为体育球员命名模板）
4. 点击「AI 分析文件名」→ 预览 → 「应用 AI 重命名」

> API Key 仅存储在内存中，关闭程序后清除（安全考虑）
> 文件名列表将发送到 DeepSeek API 进行分析

---

## 📋 依赖 Dependencies

| 依赖 | 版本 | 用途 |
|:---|:---|:---|
| Python | ≥ 3.7 | Runtime |
| [Pillow](https://python-pillow.org) | ≥ 9.0 | Image processing |
| tkinter | built-in | GUI |
| urllib | built-in | DeepSeek API |
| pytest | optional | Testing |

---

## 🏗️ 项目结构 Project Structure

```
ImgBatch/
├── imgbatch/                      # 核心包
│   ├── __init__.py
│   ├── core/                      # 无 GUI 依赖的业务逻辑
│   │   ├── common.py              # 共享常量和工具函数
│   │   ├── compress.py            # 压缩逻辑
│   │   ├── convert.py             # 格式转换
│   │   ├── rename.py              # 重命名（含冲突检测）
│   │   ├── watermark.py           # 水印
│   │   ├── trim.py                # 裁剪透明边距
│   │   ├── normalize.py           # 规范化
│   │   ├── inspect.py             # 检查
│   │   └── ai_rename.py           # AI 重命名（DeepSeek）
│   ├── ui/                        # tkinter UI 层
│   │   ├── app.py                 # 主应用窗口
│   │   ├── theme.py               # XP Classic 主题
│   │   └── widgets/
│   │       └── backup_mgr.py      # 备份管理
│   ├── infra/                     # 基础设施
│   │   ├── logger.py              # 结构化日志
│   │   ├── settings.py            # 设置持久化 (config.json)
│   │   ├── i18n.py                # 国际化 (zh/en)
│   │   └── threading.py           # 线程管理（取消/池/ETA）
│   ├── cli/                       # 命令行接口
│   │   └── main.py
│   └── history.py                 # 操作历史与撤销
├── tests/                         # 测试套件
│   ├── conftest.py                # pytest fixtures
│   ├── test_compress.py           # 压缩测试
│   ├── test_rename.py             # 重命名测试
│   ├── test_image_ops.py          # 水印/裁剪/规范化/检查测试
│   ├── test_infra.py             # 设置/i18n/日志测试
│   ├── test_history.py            # 操作历史测试
│   └── test_ai_rename.py          # AI 重命名解析测试
├── skills/
│   └── imgbatch-cli/
│       └── SKILL.md               # Agent skill 定义
├── image_compressor.pyw           # GUI 入口（向后兼容）
├── build.py                       # EXE 打包脚本
├── 启动.bat                       # 启动器
├── README.md                      # 文档
├── 说明.txt                       # 中文说明
└── memory/                        # CEO 评审记录
    └── ceo-review-summary.md
```

---

## 🏗️ 架构设计 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层 (UI)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Compress │ │ Convert  │ │ Rename   │ │Watermark │  ...   │
│  │   Tab    │ │   Tab    │ │   Tab    │ │   Tab    │       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
│       └────────────┴────────────┴────────────┘              │
│                         │                                    │
│  ┌──────────────────────┴───────────────────────────┐       │
│  │          TaskRunner (取消/池/锁/ETA)               │       │
│  └──────────────────────┬───────────────────────────┘       │
└──────────────────────────┼──────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                    核心业务逻辑层 (Core)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │compress  │ │convert   │ │rename    │ │watermark │  ...   │
│  │  .py     │ │  .py     │ │  .py     │ │  .py     │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                         │                                    │
│  ┌──────────────────────┴───────────────────────────┐       │
│  │              common.py (共享工具)                  │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                    基础设施层 (Infra)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ logger   │ │settings  │ │  i18n    │ │threading │       │
│  │  .py     │ │  .py     │ │  .py     │ │  .py     │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
```

**设计原则：**
- **核心层零 GUI 依赖** — 所有图片处理逻辑可独立测试和复用
- **UI 层只负责参数收集和结果展示** — 不包含业务逻辑
- **线程安全** — TaskRunner 提供取消、进度、ETA，try/finally 保证状态一致性
- **可观测性** — 所有操作记录到日志文件，出错可追溯

---

## 📄 License

[MIT](LICENSE) · 自由使用、修改、分发

  target_file: c:\Users\Administrator\Desktop\ImgBatch\README.md
  code_edit: <div align="center">

<img src="screenshot.png" alt="ImgBatch" width="600" />

# ImgBatch v2.0

### 全能图片批处理工具箱 · All-in-One Batch Image Toolkit

压缩 · 格式转换 · 批量重命名 · 水印 · AI 智能重命名 · 裁剪透明 · 规范化 · 检查
*Compress · Convert · Rename · Watermark · AI Rename · Trim · Normalize · Inspect*

[![Python](https://img.shields.io/badge/Python-3.7+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Pillow](https://img.shields.io/badge/Pillow-9.0+-darkgreen)](https://python-pillow.org)
[![DeepSeek](https://img.shields.io/badge/AI-DeepSeek-4D6BFE)](https://deepseek.com)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)]()
[![Tests](https://img.shields.io/badge/Tests-pytest-success)](tests/)

</div>

---

## 🆕 v2.0 新特性 · What's New

| 特性 | 说明 |
|:---|:---|
| 🏗️ **模块化架构** | 业务逻辑与 UI 完全分离，核心层无 GUI 依赖，可独立测试 |
| 💾 **设置持久化** | 所有参数自动保存到 `~/.imgbatch/config.json`，重启不丢失 |
| 📝 **结构化日志** | 所有操作和错误记录到 `~/.imgbatch/imgbatch.log` |
| 🧪 **单元测试** | 核心逻辑 100% 测试覆盖，pytest 测试套件 |
| 🔒 **线程安全** | 取消机制 + ThreadPoolExecutor + try/finally 保证状态一致性 |
| ↩️ **操作撤销** | Ctrl+Z 撤销上次操作，支持重命名和备份恢复 |
| 🌐 **i18n 完整化** | 所有 UI 文本通过翻译系统，语言切换不再丢失状态 |
| ⚡ **CLI 接口** | 无 GUI 批量处理，支持自动化脚本和 CI/CD |
| 🤖 **Agent Skill** | 内置 AI agent skill，可被编程助手调用 |
| 🔄 **递归扫描** | 支持子目录递归扫描图片 |
| 📊 **ETA 估算** | 实时显示预计剩余时间 |
| 📋 **EXIF 控制** | 保留 / 清除 / 仅方向 三种 EXIF 处理模式 |
| 🛡️ **冲突检测** | 重命名时自动检测文件名冲突，支持跳过/覆盖/自动序号 |
| 🎯 **多格式预估** | 压缩预览按格式分组采样，多格式混合预估更准确 |
| 🔁 **AI 加固** | DeepSeek API 3 次指数退避重试 + 响应验证 + 分批发送 + token 追踪 |

---

## ✨ 八大核心功能 · Eight Core Modules

<table>
<tr>
<td width="50%">

### 🗜️ 压缩 Compress
- 质量 1%–100% 无级调节
- 缩放比例 10%–100%
- EXIF 保留 / 清除 / 仅方向
- 替换原文件 / 输出新文件夹
- 自动备份 + 备份管理（恢复/清除）
- 实时大小预估（多格式分组采样）
- 支持同步格式转换 / 重命名 / 水印

### 🔄 格式转换 Format
- JPG ⇄ PNG ⇄ WEBP ⇄ BMP ⇄ TIFF ⇄ GIF ⇄ ICO
- 智能透明度处理（RGBA→RGB）
- 可替换原文件或输出到新目录

### 🏷️ 批量重命名 Rename
- 添加前缀 / 后缀
- 查找替换文本
- 序号模板 `photo_{num}`（自定义位数+起始值）
- 全大写 / 全小写转换
- **冲突检测**（跳过/覆盖/自动加序号）
- 实时预览

### 💧 水印 Watermark
- 文字水印：内容、字号、颜色(#HEX)、透明度
- 图片水印：PNG LOGO、缩放比例、透明度
- 位置：左上/右上/居中/左下/右下
- 支持备份和双输出模式

</td>
<td width="50%">

### 🤖 AI 智能重命名 AI Rename
- 接入 **DeepSeek** API
- 自定义提示词
- 预览 AI 建议 → 一键应用
- **3 次指数退避重试**
- **响应结构验证**
- **分批发送**（每批最多 100 个文件名）
- **Token 用量追踪**
- 本地调用，不上传服务器

### ✂️ 裁剪透明 Trim Alpha
- 裁剪 PNG 透明边距
- 自定义边距 padding
- 支持备份和双输出模式

### 🔍 检查 Inspect
- 检查 PNG 画布尺寸 / 内容尺寸
- 上下左右边距分析
- 批量结果表格展示

### 📐 规范化 Normalize
- Alpha 阈值裁剪
- 统一目标高度缩放
- 均匀透明边距
- 适用于标题图片统一规格

</td>
</tr>
</table>

---

## 🚀 快速开始 Quick Start

### GUI 模式

```bash
# 安装依赖
pip install Pillow

# 运行 GUI
python image_compressor.pyw
```

> 双击 `启动.bat` 一键启动

### CLI 模式

```bash
# 压缩
python -m imgbatch.cli compress -f ./photos --quality 75 --resize 50

# 格式转换
python -m imgbatch.cli convert -f ./photos --to webp

# 批量重命名
python -m imgbatch.cli rename -f ./photos --mode seq --template "photo_{num}" --start 1

# 水印
python -m imgbatch.cli watermark -f ./photos --text "© 2026" --opacity 50

# 裁剪透明边距
python -m imgbatch.cli trim -f ./pngs --padding 4

# 规范化
python -m imgbatch.cli normalize -f ./pngs --target-height 280

# 检查 PNG
python -m imgbatch.cli inspect -f ./pngs

# AI 重命名
python -m imgbatch.cli ai-rename -f ./photos --api-key sk-xxx --apply
```

### 运行测试

```bash
pip install pytest
pytest tests/ -v
```

### 📦 打包为 EXE Build to EXE

```bash
# 一键打包（自动检测 imgbatch 包所有子模块）
build.bat

# 或手动执行
pip install pyinstaller
python build.py
```

> 输出文件在 `dist/ImgBatch.exe`，单文件便携，无需安装 Python

---

## 🔑 AI 重命名配置

1. 获取 [DeepSeek API Key](https://platform.deepseek.com/api_keys)
2. 粘贴到「AI重命名」标签页
3. 可自定义提示词（默认为体育球员命名模板）
4. 点击「AI 分析文件名」→ 预览 → 「应用 AI 重命名」

> API Key 仅存储在内存中，关闭程序后清除（安全考虑）
> 文件名列表将发送到 DeepSeek API 进行分析

---

## 📋 依赖 Dependencies

| 依赖 | 版本 | 用途 |
|:---|:---|:---|
| Python | ≥ 3.7 | Runtime |
| [Pillow](https://python-pillow.org) | ≥ 9.0 | Image processing |
| tkinter | built-in | GUI |
| urllib | built-in | DeepSeek API |
| pytest | optional | Testing |

---

## 🏗️ 项目结构 Project Structure

```
ImgBatch/
├── imgbatch/                      # 核心包
│   ├── __init__.py
│   ├── core/                      # 无 GUI 依赖的业务逻辑
│   │   ├── common.py              # 共享常量和工具函数
│   │   ├── compress.py            # 压缩逻辑
│   │   ├── convert.py             # 格式转换
│   │   ├── rename.py              # 重命名（含冲突检测）
│   │   ├── watermark.py           # 水印
│   │   ├── trim.py                # 裁剪透明边距
│   │   ├── normalize.py           # 规范化
│   │   ├── inspect.py             # 检查
│   │   └── ai_rename.py           # AI 重命名（DeepSeek）
│   ├── ui/                        # tkinter UI 层
│   │   ├── app.py                 # 主应用窗口
│   │   ├── theme.py               # XP Classic 主题
│   │   └── widgets/
│   │       └── backup_mgr.py      # 备份管理
│   ├── infra/                     # 基础设施
│   │   ├── logger.py              # 结构化日志
│   │   ├── settings.py            # 设置持久化 (config.json)
│   │   ├── i18n.py                # 国际化 (zh/en)
│   │   └── threading.py           # 线程管理（取消/池/ETA）
│   ├── cli/                       # 命令行接口
│   │   └── main.py
│   └── history.py                 # 操作历史与撤销
├── tests/                         # 测试套件
│   ├── conftest.py                # pytest fixtures
│   ├── test_compress.py           # 压缩测试
│   ├── test_rename.py             # 重命名测试
│   ├── test_image_ops.py          # 水印/裁剪/规范化/检查测试
│   ├── test_infra.py             # 设置/i18n/日志测试
│   ├── test_history.py            # 操作历史测试
│   └── test_ai_rename.py          # AI 重命名解析测试
├── skills/
│   └── imgbatch-cli/
│       └── SKILL.md               # Agent skill 定义
├── image_compressor.pyw           # GUI 入口（向后兼容）
├── build.py                       # EXE 打包脚本
├── 启动.bat                       # 启动器
├── README.md                      # 文档
├── 说明.txt                       # 中文说明
└── memory/                        # CEO 评审记录
    └── ceo-review-summary.md
```

---

## 🏗️ 架构设计 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层 (UI)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Compress │ │ Convert  │ │ Rename   │ │Watermark │  ...   │
│  │   Tab    │ │   Tab    │ │   Tab    │ │   Tab    │       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
│       └────────────┴────────────┴────────────┘              │
│                         │                                    │
│  ┌──────────────────────┴───────────────────────────┐       │
│  │          TaskRunner (取消/池/锁/ETA)               │       │
│  └──────────────────────┬───────────────────────────┘       │
└──────────────────────────┼──────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                    核心业务逻辑层 (Core)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │compress  │ │convert   │ │rename    │ │watermark │  ...   │
│  │  .py     │ │  .py     │ │  .py     │ │  .py     │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                         │                                    │
│  ┌──────────────────────┴───────────────────────────┐       │
│  │              common.py (共享工具)                  │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                    基础设施层 (Infra)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ logger   │ │settings  │ │  i18n    │ │threading │       │
│  │  .py     │ │  .py     │ │  .py     │ │  .py     │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
```

**设计原则：**
- **核心层零 GUI 依赖** — 所有图片处理逻辑可独立测试和复用
- **UI 层只负责参数收集和结果展示** — 不包含业务逻辑
- **线程安全** — TaskRunner 提供取消、进度、ETA，try/finally 保证状态一致性
- **可观测性** — 所有操作记录到日志文件，出错可追溯

---

## 📄 License

[MIT](LICENSE) · 自由使用、修改、分发

