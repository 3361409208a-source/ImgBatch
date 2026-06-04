<div align="center">

<img src="screenshot.png" alt="ImgBatch" width="600" />

# ImgBatch

### 全能图片批处理工具箱 · All-in-One Batch Image Toolkit

压缩 · 格式转换 · 批量重命名 · 水印 · AI 智能重命名  
*Compress · Convert · Rename · Watermark · AI Rename*

[![Python](https://img.shields.io/badge/Python-3.7+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Pillow](https://img.shields.io/badge/Pillow-9.0+-darkgreen)](https://python-pillow.org)
[![DeepSeek](https://img.shields.io/badge/AI-DeepSeek-4D6BFE)](https://deepseek.com)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)]()

</div>

---

## ✨ 五大核心功能 · Five Core Modules

<table>
<tr>
<td width="50%">

### 🗜️ 压缩 Compress
- 质量 1%–100% 无级调节
- 缩放比例 10%–100%
- 替换原文件 / 输出新文件夹
- 自动备份 + 备份管理（恢复/清除）
- 支持 JPG · PNG · WEBP · BMP · TIFF · GIF · ICO

### 🔄 格式转换 Format
- JPG ⇄ PNG ⇄ WEBP ⇄ BMP ⇄ TIFF ⇄ GIF ⇄ ICO
- 智能透明度处理（RGBA→RGB）
- 可替换原文件或输出到新目录

### 🏷️ 批量重命名 Rename
- 添加前缀 / 后缀
- 查找替换文本
- 序号模板 `photo_{num}`（自定义位数+起始值）
- 全大写 / 全小写转换
- 实时预览

</td>
<td width="50%">

### 🗜️ Compress
- Quality slider 1%–100%
- Resize slider 10%–100%
- Replace or export to folder
- Auto-backup with timestamp

### 🔄 Format Convert
- All formats interchangeable
- Smart alpha channel handling
- Replace or export

### 🏷️ Batch Rename
- Prefix / suffix / find-replace
- Sequential numbering `{num}`
- Upper / lower case
- Live preview

</td>
</tr>
<tr>
<td>

### 💧 水印 Watermark
- 文字水印：内容、字号、颜色(#HEX)、透明度
- 图片水印：PNG LOGO、缩放比例、透明度
- 位置：左上/右上/居中/左下/右下
- 支持备份和双输出模式

### 🤖 AI 智能重命名 AI Rename
- 接入 **DeepSeek** API
- 自定义提示词（默认生成 `player-position-country.ext`）
- 预览 AI 建议 → 一键应用
- 自行设置 API Key（本地调用，不上传服务器）

</td>
<td>

### 💧 Watermark
- Text: content, size, color, opacity
- Image: PNG logo, scale, opacity
- 5 positions: corners + center
- Backup + dual output

### 🤖 AI Rename (DeepSeek)
- Powered by **DeepSeek** API
- Custom prompt
- Preview suggestions → apply with one click
- Local API call, no data collection

</td>
</tr>
</table>

---

## 🚀 快速开始 Quick Start

```bash
# 安装依赖
pip install Pillow

# 运行
python image_compressor.pyw
```

> 双击 `启动.bat` 一键启动  
> *Double-click `启动.bat`*

### 📦 打包为 EXE Build to EXE

```bash
# 一键打包（自带 PyInstaller 安装检测）
build.bat

# 或在终端手动执行
pip install pyinstaller
pyinstaller --onefile --windowed --name ImgBatch image_compressor.pyw
```

> 输出文件在 `dist/ImgBatch.exe`，单文件便携，无需安装 Python

---

## 🔑 AI 重命名配置

1. 获取 [DeepSeek API Key](https://platform.deepseek.com/api_keys)
2. 粘贴到「AI重命名」标签页
3. 可自定义提示词（默认为体育球员命名模板）
4. 点击「AI 分析文件名」→ 预览 → 「应用 AI 重命名」

---

## 📋 依赖 Dependencies

| 依赖 | 版本 | 用途 |
|:---|:---|:---|
| Python | ≥ 3.7 | Runtime |
| [Pillow](https://python-pillow.org) | ≥ 9.0 | Image processing |
| tkinter | built-in | GUI |
| urllib | built-in | DeepSeek API |

---

## 🏗️ 项目结构

```
ImgBatch/
├── image_compressor.pyw    # 主程序
├── 启动.bat                # 启动器
├── build.bat               # 一键打包 EXE
├── README.md               # 文档
└── 说明.txt                # 中文说明
```

---

## 📄 License

[MIT](LICENSE) · 自由使用、修改、分发

