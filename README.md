<div align="center">

<img src="screenshot.png" alt="ImgBatch" width="600" />

# ImgBatch v3.0

### 全能图片批处理工具箱 · All-in-One Batch Image Toolkit

压缩 · 格式转换 · 文档转换 · 重命名 · 水印 · AI 重命名 · 裁剪透明 · 检查 · 规范化 · 精灵图 · GIF 编辑 · 视频转动图 · 抠图

[![Tauri](https://img.shields.io/badge/Tauri-2-24C8DB?logo=tauri&logoColor=white)](https://tauri.app)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Python](https://img.shields.io/badge/Python-3.7+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Pillow](https://img.shields.io/badge/Pillow-9.0+-darkgreen)](https://python-pillow.org)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)]()

[官网 / Website](website/) · [下载 Releases](https://github.com/3361409208a-source/ImgBatch/releases/latest)

</div>

---

## 简介

**ImgBatch 3.0** 是基于 **Tauri 2 + React + Python** 的 Windows 桌面批处理工具。图片处理逻辑在本地 Python 核心中执行，通过 HTTP API 侧车与前端通信；支持主窗口精细操作、资源管理器**右键菜单**与**快捷弹窗**三种工作流。

所有图片处理在本地完成，不上传云端（AI 重命名可选 DeepSeek API 或秘塔 AI 助手）。

---

## v3.0 新特性

| 特性 | 说明 |
|:---|:---|
| 🖥️ **Tauri 桌面应用** | 现代 React UI，轻量安装包，NSIS 安装器 |
| 🖱️ **资源管理器右键** | 压缩 / 转换 / 重命名 / 水印 / 裁边 / 规范化 / 检查 / GIF — 每项独立菜单，各自带子选项 |
| ⚡ **快捷弹窗** | 右键 `--quick` 启动精简窗口，预填文件与动作，一键执行 |
| 🎞️ **GIF 动图编辑** | 优化、缩放、减色、变速、倒放、裁透明边、水印、拆帧等 |
| 🎬 **视频转动图** | WebM/MP4/MOV 等转为动画 WebP 或 GIF；支持**白底抠图**输出透明背景 GIF |
| ✂️ **抠图** | AI 模型抠图（需要扩展包） |
| 🧩 **精灵图** | 智能排列、间距、2 的幂次画布、导出 JSON 坐标 |
| 🤖 **AI 重命名增强** | DeepSeek 一键分析；无 API Key 时可打开秘塔 AI，自动填入需求并粘贴 JSON 解析 |
| ↩️ **撤销与备份** | 操作撤销、自动备份、备份管理 |
| 🔧 **一键安装 FFmpeg** | 需要 FFmpeg 的功能可一键下载便携版到本地扩展目录，无需系统全局安装 |
| 🌐 **中英双语** | 界面 i18n 完整覆盖 |

---

## 十二大功能模块

| 模块 | 能力摘要 |
|:---|:---|
| **压缩** | 质量/缩放调节、EXIF 控制、大小预估、备份 |
| **格式转换** | 常用预设 + JPG / PNG / WEBP / AVIF / BMP / TIFF / GIF / ICO；支持 HEIC 输入 |
| **文档转换** | 内置 PDF/CSV 能力；**Office 扩展包**可一键从官方直链下载解压至 `%USERPROFILE%\.imgbatch\extensions\` |
| **批量重命名** | 前缀后缀、查找替换、序号、大小写、冲突检测、预览 |
| **水印** | 文字/图片水印，位置、透明度、缩放 |
| **AI 重命名** | DeepSeek API 或秘塔 AI 助手 + JSON 粘贴解析 |
| **裁剪透明** | PNG 透明边裁剪，自定义 padding |
| **检查** | PNG 画布/内容尺寸与四周边距分析 |
| **规范化** | Alpha 阈值、统一高度、均匀边距 |
| **精灵图** | 多图合并为雪碧图，可选 JSON 坐标 |
| **GIF 编辑** | 动图优化、缩放、减色、变速、倒放、裁边、水印、拆帧 |
| **视频转动图** | WebM/MP4/MOV → WebP/GIF；**白底抠图**输出透明背景 GIF，可调白底相似度与边缘混合 |
| **抠图** | AI 模型抠图（需要扩展包） |

---

## 快速开始

### 环境要求

- Windows 10/11
- [Node.js](https://nodejs.org) 18+
- [Rust](https://rustup.rs)（Tauri 构建）
- Python 3.7+（开发 / 侧车）

### 开发运行

```powershell
git clone https://github.com/3361409208a-source/ImgBatch.git
cd ImgBatch
npm install --prefix frontend
npm run tauri dev
```

### 构建安装包

```powershell
.\scripts\build-tauri.ps1
# 输出: src-tauri\target\release\bundle\nsis\ImgBatch_3.0.0_x64-setup.exe
```

### 注册右键菜单（开发态）

```powershell
.\scripts\register-context-menu.ps1
# 或管理员修复 HKLM:
.\scripts\fix-hklm-context-menu.ps1
taskkill /f /im explorer.exe; start explorer.exe
```

### 运行测试

```powershell
pip install pytest
pytest tests/ -v
```

### 官网本地预览

```powershell
cd website
npm install
npm run dev
```

部署说明见 [website/README.md](website/README.md)。

---

## AI 重命名

**方式一：DeepSeek API**

1. 在 [DeepSeek](https://platform.deepseek.com/api_keys) 获取 API Key
2. 填写 Key →「AI 分析文件名」→ 预览 →「应用 AI 重命名」

**方式二：秘塔 AI（无需 API Key）**

1. 填写「命名要求」（只需描述风格，JSON 格式由系统自动附加）
2. 点击「秘塔 AI 助手」→ 自动打开 metaso.cn 并填入完整需求
3. 复制 AI 返回的 JSON → 粘贴到解析区 →「解析并预览」→ 应用

---

## CLI（可选）

仍支持无 GUI 命令行批处理：

```bash
python -m imgbatch.cli compress -f ./photos --quality 75
python -m imgbatch.cli convert -f ./photos --to webp
python -m imgbatch.cli ai-rename -f ./photos --api-key sk-xxx --apply
python -m imgbatch.cli video-anim -f ./videos --to .gif --white-key
```

---

## 项目结构

```
ImgBatch/
├── frontend/                 # React + Vite 主界面
├── src-tauri/                # Tauri 2 壳（Rust）
├── imgbatch/                 # Python 核心 + API 侧车
│   ├── core/                 # 图片处理逻辑（含 video_anim / matting）
│   ├── api/                  # FastAPI 路由
│   ├── cli/                  # 命令行
│   └── infra/                # 基础组件（日志、配置）
├── website/                  # 官方落地页（Vercel）
├── scripts/                  # 构建、右键菜单注册脚本
└── tests/                    # pytest 测试
```

---

## 架构

```
React UI (Tauri WebView)
        │ invoke / events
        ▼
Rust Shell (窗口、右键、秘塔 WebView)
        │ sidecar spawn
        ▼
Python API (FastAPI @ localhost)
        │
        ▼
imgbatch.core.* (Pillow 批处理)
```

---

## License

[MIT](LICENSE)
