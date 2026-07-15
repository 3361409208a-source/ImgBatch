# ImgBatch Tauri + React + Python Sidecar 迁移开发手册

> **读者：** 执行本迁移的 AI 或开发者  
> **目标：** 将现有 Tkinter GUI 替换为 `React 前端 + Tauri 2 Rust 壳 + Python sidecar`  
> **分支：** `feat/tauri-react`（从 `main` 拉出，完成后 PR）  
> **原则：** 不修改 `imgbatch/core/` 业务逻辑；只新增 API 层和前端；CLI 保留  
> **UI 技能：** 前端界面必须使用 [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) 生成设计系统并指导实现（见 0.5 节）  

---

## 0. 开始前必读

### 0.1 现有代码地图（不要重复造轮子）

| 路径 | 作用 | 迁移时 |
|------|------|--------|
| `imgbatch/core/*.py` | 压缩/转换/重命名等业务 | **只调用，不改** |
| `imgbatch/cli/main.py` | 命令行入口 | **保留** |
| `imgbatch/infra/settings.py` | `~/.imgbatch/config.json` | API 读写 |
| `imgbatch/infra/i18n.py` | 中英翻译字典 `TRANSLATIONS` | 导出到前端 JSON |
| `imgbatch/history.py` | 撤销/历史 | API `/undo` |
| `imgbatch/ui/widgets/backup_mgr.py` | 备份逻辑 | API 调用 `create_backup` 等 |
| `imgbatch/ui/app.py` | 旧 Tkinter UI（约 2100 行） | **最后删除** |
| `image_compressor.pyw` | 旧 GUI 入口 | **最后删除** |

### 0.2 必须实现的 9 个功能页（与现 Tkinter 一一对应）

1. 压缩 `compress`
2. 格式转换 `convert`
3. 重命名 `rename`
4. 水印 `watermark`
5. AI 重命名 `ai_rename`
6. 裁剪透明边 `trim`
7. 检查 `inspect`
8. 规范化 `normalize`
9. 精灵图 `spritesheet`

### 0.3 开发环境（全部装好再动手）

```powershell
# Python 3.10+
python --version

# Node 20+
node --version

# Rust stable
rustc --version

# 安装 Tauri CLI（全局一次）
cargo install tauri-cli --version "^2"

# Python 新依赖（写入 requirements-api.txt）
pip install fastapi uvicorn pydantic sse-starlette
```

### 0.5 安装 UI 技能（前端开发强制依赖）

前端所有页面、组件、配色、字体、间距**必须**遵循本技能生成的设计系统，禁止 AI 凭感觉随意写 CSS。

**技能仓库：** https://github.com/nextlevelbuilder/ui-ux-pro-max-skill

#### 0.5.1 人类用户执行一次（AI 不得自行 npm install -g，应提示用户执行）

```powershell
npm install -g ui-ux-pro-max-cli
cd C:\Users\Administrator\Desktop\ImgBatch
uipro init --ai cursor
# 或全局安装到所有项目：
# uipro init --ai cursor --global
```

安装后技能位于 `.cursor/skills/ui-ux-pro-max/`（或 `~/.cursor/skills/`）。

#### 0.5.2 AI 开发前必须做的事

1. **读取技能文件：** `.cursor/skills/ui-ux-pro-max/SKILL.md`（若不存在，提示用户先执行 0.5.1）
2. **生成并持久化设计系统**（在项目根目录执行）：

```powershell
python .cursor/skills/ui-ux-pro-max/scripts/search.py "photo batch image processing desktop tool dashboard" --design-system --persist -p "ImgBatch" --stack react
```

可选：为各页面生成 override 文件：

```powershell
python .cursor/skills/ui-ux-pro-max/scripts/search.py "file list table filter toolbar" --design-system --persist -p "ImgBatch" --page "workspace" --stack react
python .cursor/skills/ui-ux-pro-max/scripts/search.py "batch operation form settings panel" --design-system --persist -p "ImgBatch" --page "compress" --stack react
```

3. **产出目录**（纳入 git）：

```
frontend/design-system/
├── MASTER.md              # 全局：颜色、字体、圆角、阴影、组件规范
└── pages/
    ├── workspace.md       # 文件列表 + 筛选 + 预览
    ├── compress.md
    ├── convert.md
    └── ...                  # 其余 Tab 各一份（可选）
```

4. **写任何 React 组件前**，在 prompt 中声明：

```
我正在实现 ImgBatch 的 [页面名]。
请先阅读 frontend/design-system/MASTER.md，
再检查 frontend/design-system/pages/[page-name].md 是否存在并优先采用。
技术栈：React 18 + TypeScript + Tailwind CSS + Tauri 2 桌面窗口（最小宽度 880px）。
图标使用 Lucide React，禁止用 emoji 当图标。
```

#### 0.5.3 ImgBatch 推荐设计方向（供 search.py 关键词参考）

| 维度 | 建议 |
|------|------|
| 产品类型 | Photo / Video Editor、Developer Tool、Productivity Dashboard |
| 风格 | Minimalism & Swiss Style 或 Soft UI Evolution（工具类、信息密度高） |
| 模式 | Feature-Rich Showcase + Data-Dense Dashboard（文件表 + 多 Tab 设置） |
| 避免 | 霓虹渐变、过度动效、低对比度灰色文字、emoji 图标 |

#### 0.5.4 技能交付检查清单（每个 Page 完成前对照）

技能内置 Pre-delivery Checklist，桌面端至少满足：

- [ ] 可点击元素有 `cursor-pointer` 和 hover 过渡（150–300ms）
- [ ] 正文对比度 ≥ 4.5:1（WCAG AA）
- [ ] 键盘 focus 态可见（`focus-visible:ring`）
- [ ] 图标统一用 Lucide SVG，不用 emoji
- [ ] 支持 `prefers-reduced-motion`
- [ ] 布局在 880px / 1000px / 1280px 宽度下不崩（Tauri 默认窗口可缩放）

#### 0.5.5 前端技术栈（与技能对齐）

```text
React 18 + TypeScript + Vite
Tailwind CSS 3.x
Lucide React（图标）
shadcn/ui（可选，与技能 React 栈指南一致时再引入）
Zustand（状态）
@tanstack/react-virtual（大文件列表）
react-i18next（中英）
```

**不要**引入 MUI / Ant Design（与技能设计系统冲突，且体积大）。

### 0.6 创建分支

```powershell
cd C:\Users\Administrator\Desktop\ImgBatch
git checkout main
git pull
git checkout -b feat/tauri-react
```

---

## 1. 目标架构

```
用户双击 ImgBatch.exe
    │
    ▼
Tauri (Rust) ──启动──► Python sidecar (imgbatch-api.exe)
    │                        │
    │                        ▼
    │                   FastAPI @ 127.0.0.1:随机端口
    │                        │
    ▼                        ▼
WebView 加载 React      imgbatch/core/* 执行业务
    │
    └── HTTP + SSE 与 Python 通信
```

**分工硬规则：**

- **Tauri/Rust 只做：** 窗口、系统文件对话框、打开资源管理器、拖拽路径、启动/杀死 sidecar
- **Python 只做：** 扫盘、图片处理、配置、日志、历史、备份
- **React 只做：** 界面、调 API、展示进度；**视觉规范遵循 `frontend/design-system/`**

---

## 2. 最终目录结构（按此创建文件）

```
ImgBatch/
├── docs/
│   └── TAURI_MIGRATION.md          # 本文档
├── imgbatch/
│   ├── api/                        # 【新增】
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app + uvicorn 入口
│   │   ├── schemas.py              # Pydantic 模型
│   │   ├── tasks.py                # 任务管理 + SSE
│   │   ├── deps.py                 # 单例 TaskRunner 等
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py
│   │       ├── config.py
│   │       ├── scan.py
│   │       ├── preview.py
│   │       ├── tasks.py
│   │       ├── backups.py
│   │       └── undo.py
│   ├── core/                       # 不动
│   └── ui/                         # 迁移完成后删除
├── frontend/                       # 【新增】React
│   ├── design-system/              # 【技能生成】UI 规范（MASTER + pages）
│   │   ├── MASTER.md
│   │   └── pages/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/
│       │   ├── client.ts           # fetch 封装
│       │   ├── types.ts            # TS 类型（与 schemas 对齐）
│       │   └── sse.ts              # SSE 进度订阅
│       ├── store/
│       │   └── appStore.ts         # Zustand：folder, files, task, config
│       ├── components/
│       │   ├── FolderBar.tsx
│       │   ├── FilterBar.tsx
│       │   ├── FileTable.tsx
│       │   ├── PreviewPanel.tsx
│       │   ├── TaskProgress.tsx
│       │   ├── OutputOptions.tsx   # 替换原文件 / 输出到 / 备份
│       │   └── TabLayout.tsx
│       ├── pages/
│       │   ├── CompressPage.tsx
│       │   ├── ConvertPage.tsx
│       │   ├── RenamePage.tsx
│       │   ├── WatermarkPage.tsx
│       │   ├── AiRenamePage.tsx
│       │   ├── TrimPage.tsx
│       │   ├── InspectPage.tsx
│       │   ├── NormalizePage.tsx
│       │   └── SpritesheetPage.tsx
│       ├── i18n/
│       │   ├── index.ts
│       │   ├── zh.json
│       │   └── en.json
│       └── styles/
│           └── globals.css
├── src-tauri/                      # 【新增】Tauri 2
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── build.rs
│   ├── binaries/                   # PyInstaller 产出放这里
│   │   └── imgbatch-api-x86_64-pc-windows-msvc.exe
│   └── src/
│       ├── main.rs
│       ├── lib.rs
│       ├── sidecar.rs
│       └── commands.rs
├── scripts/
│   ├── build-sidecar.ps1
│   ├── build-frontend.ps1
│   └── build-tauri.ps1
├── imgbatch-api.spec               # 【新增】PyInstaller spec（无 tkinter）
└── requirements-api.txt            # 【新增】
```

---

## 3. 阶段一：Python API 层（先做，可独立 curl 测试）

### 3.1 创建 `requirements-api.txt`

```text
fastapi>=0.110
uvicorn[standard]>=0.27
pydantic>=2.0
sse-starlette>=2.0
Pillow>=9.0
```

### 3.2 创建 `imgbatch/api/schemas.py`（完整类型定义）

以下 JSON 字段名**禁止改名**，前端将严格对齐。

```python
# 文件信息（与 core/common.scan_folder 返回一致）
class FileInfo(BaseModel):
    name: str          # 相对路径，如 colorful/promo/a.png
    path: str          # 绝对路径
    size: int
    size_str: str
    dimensions: str    # "1920x1080" 或 "?"
    format: str

# POST /scan
class ScanRequest(BaseModel):
    folder: str
    recursive: bool = False

class ScanResponse(BaseModel):
    files: list[FileInfo]

# POST /filter
class FilterRequest(BaseModel):
    files: list[FileInfo]
    name_query: str = ""
    format: str = "ALL"       # ALL | PNG | JPEG | ...
    size_preset: str = "all"    # 对应 SIZE_PRESETS 的 key
    size_min_kb: str = ""
    size_max_kb: str = ""
    min_width: str = ""
    min_height: str = ""

# POST /compress/estimate
class CompressEstimateRequest(BaseModel):
    files: list[FileInfo]
    quality: int = 75
    resize_pct: int = 100

class CompressEstimateResponse(BaseModel):
    total_before: int
    total_after: int

# POST /tasks  —— 统一任务创建
class TaskCreateRequest(BaseModel):
    type: Literal[
        "compress", "convert", "rename", "watermark",
        "ai_rename", "ai_apply", "trim", "inspect",
        "normalize", "spritesheet"
    ]
    folder: str
    file_list: list[str]        # 相对路径名列表
  # 以下按 type 选填，见 3.4 节各任务参数表
    params: dict = {}

class TaskCreateResponse(BaseModel):
    task_id: str

# SSE 事件 data  JSON
class TaskProgressEvent(BaseModel):
    pct: float
    message: str

class TaskDoneEvent(BaseModel):
    status: Literal["done", "error", "cancelled"]
    result: dict
```

### 3.3 创建 `imgbatch/api/tasks.py`（任务管理器）

**必须行为：**

1. 全局同时只允许 **1 个** 运行中任务（与现 `TaskRunner` 一致）
2. 每个任务有 UUID `task_id`
3. 进度写入 `asyncio.Queue`，SSE 端点读取
4. 取消：设置 `TaskState.cancel()`，与 `imgbatch/infra/threading.py` 相同

**伪代码骨架（照此实现）：**

```python
import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional
from imgbatch.infra.threading import TaskState

@dataclass
class TaskRecord:
    id: str
    state: TaskState
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    result: Optional[dict] = None
    error: Optional[str] = None

class TaskManager:
    def __init__(self):
        self._current: Optional[TaskRecord] = None
        self._lock = asyncio.Lock()

    async def start(self, fn, *args, **kwargs) -> str:
        async with self._lock:
            if self._current and self._current.state.running:
                raise RuntimeError("task_already_running")
            task_id = str(uuid.uuid4())
            state = TaskState()
            record = TaskRecord(id=task_id, state=state)
            self._current = record

        def on_progress(pct, msg):
            record.queue.put_nowait({"type": "progress", "pct": pct, "message": msg})

        def run_in_thread():
            try:
                result = fn(state, *args, on_progress=on_progress, **kwargs)
                record.result = result
                record.queue.put_nowait({"type": "done", "status": "done", "result": result})
            except Exception as exc:
                record.error = str(exc)
                record.queue.put_nowait({"type": "done", "status": "error", "result": {"error": str(exc)}})
            finally:
                state.set_running(False)

        state.set_running(True)
        asyncio.get_event_loop().run_in_executor(None, run_in_thread)
        return task_id

    def cancel(self, task_id: str) -> bool:
        if self._current and self._current.id == task_id:
            self._current.state.cancel()
            return True
        return False

task_manager = TaskManager()
```

### 3.4 各任务 `POST /tasks` 的 `params` 字段表（照抄到路由分发）

#### type = `compress`

调用：`imgbatch.core.compress.run_compress_batch`

```json
{
  "quality": 68,
  "resize_pct": 70,
  "do_backup": true,
  "replace": false,
  "out": "C:\\Users\\...\\output",
  "exif_mode": "keep",
  "options": {
    "convert": false,
    "target_fmt": ".png",
    "rename": false,
    "prefix": "",
    "suffix": "",
    "watermark": false,
    "wm_text": "",
    "wm_opacity": 0.5
  }
}
```

`backup_fn`：若 `do_backup=true`，传 `imgbatch.ui.widgets.backup_mgr.do_backup`（在 API 层 import 为 `create_backup`）。

#### type = `convert`

调用：`run_convert_batch(state, folder, file_list, target_fmt, do_backup, replace, out, ...)`

```json
{
  "target_fmt": ".webp",
  "do_backup": true,
  "replace": false,
  "out": "C:\\output"
}
```

#### type = `rename`

先 `generate_rename_map(file_data, mode, ...)` 得 mapping，再 `run_rename_batch(folder, mapping, ConflictResolution.AUTO_NUMBER, ...)`

```json
{
  "mode": "prefix",
  "prefix": "img_",
  "suffix": "",
  "find": "",
  "replace": "",
  "seq_template": "photo_{num}",
  "seq_start": 1,
  "seq_digits": 3,
  "lowercase": false,
  "uppercase": false
}
```

额外端点 `POST /rename/preview`：只返回 mapping，不执行。

#### type = `watermark`

调用：`run_watermark_batch`

```json
{
  "params": {
    "type": "text",
    "text": "水印",
    "fontsize": 36,
    "opacity": 0.5,
    "position": "bottom-right",
    "color": "#ffffff",
    "image_path": "",
    "img_scale": 0.2
  },
  "do_backup": true,
  "replace": true,
  "out": null
}
```

#### type = `ai_rename`

调用：`run_ai_rename(state, api_key, file_names, prompt)` —— **不修改文件**

```json
{
  "api_key": "sk-...",
  "prompt": "..."
}
```

返回 result 含 `results: {原文件名: 新文件名}`。

#### type = `ai_apply`

调用：`apply_ai_rename(state, folder, mapping, ...)`

```json
{
  "mapping": {"old.png": "new.png"}
}
```

#### type = `trim`

```json
{
  "padding": 4,
  "do_backup": true,
  "replace": true,
  "out": null
}
```

#### type = `inspect`

```json
{}
```

注意：只处理 PNG，传 `png_list`（完整 FileInfo dict 列表）给 `run_inspect_batch`。

#### type = `normalize`

```json
{
  "alpha_threshold": 28,
  "target_height": 280,
  "padding": 6,
  "do_backup": true,
  "replace": true,
  "out": null
}
```

#### type = `spritesheet`

调用：`imgbatch.core.spritesheet.run_spritesheet_build`

```json
{
  "image_paths": ["a.png", "b.png"],
  "output": "C:\\folder\\spritesheet.png",
  "layout": "auto",
  "spacing": 2,
  "trim": true,
  "trim_padding": 2,
  "alpha_threshold": 28,
  "columns": 0,
  "max_width": 0,
  "power_of_two": false,
  "export_json": true
}
```

### 3.5 创建 `imgbatch/api/main.py`

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ImgBatch HTTP API — Tauri sidecar entry."""

import os
import socket
from contextlib import closing

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import health, config, scan, preview, tasks, backups, undo

app = FastAPI(title="ImgBatch API", version="3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 仅 localhost，sidecar 不对外
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(config.router, prefix="/config")
app.include_router(scan.router)
app.include_router(preview.router, prefix="/preview")
app.include_router(tasks.router, prefix="/tasks")
app.include_router(backups.router, prefix="/backups")
app.include_router(undo.router, prefix="/undo")


def find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


if __name__ == "__main__":
    port = int(os.environ.get("IMG_BATCH_PORT", 0)) or find_free_port()
    print(f"IMG_BATCH_PORT={port}", flush=True)   # Tauri 必须解析这行
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
```

### 3.6 API 路由清单（全部实现，缺一不可）

| 方法 | 路径 | 实现要点 |
|------|------|----------|
| GET | `/health` | 返回 `{"ok": true}` |
| GET | `/config` | `load_config()` |
| PUT | `/config` | `save_config(body)` |
| POST | `/scan` | `scan_folder(folder, recursive)` |
| POST | `/filter` | `filter_files(...)` 复用 common.py |
| POST | `/compress/estimate` | `estimate_compressed_size(...)` |
| POST | `/rename/preview` | `generate_rename_map(...)` |
| POST | `/preview/thumb` | 读图缩略图，返回 `{"data_url": "data:image/png;base64,..."}` |
| POST | `/tasks` | 创建任务，见 3.4 |
| GET | `/tasks/{id}/events` | SSE，`text/event-stream` |
| GET | `/tasks/{id}` | 返回 result |
| DELETE | `/tasks/{id}` | 取消 |
| GET | `/backups?folder=` | `find_backups(folder)` |
| POST | `/backups/restore` | `do_restore(backup_dir, folder)` |
| DELETE | `/backups` | `do_clear_backups([...])` |
| POST | `/undo` | `history.pop()` + `undo_operation(record)` |

### 3.7 SSE 端点示例（`/tasks/{id}/events`）

```python
from sse_starlette.sse import EventSourceResponse

@router.get("/{task_id}/events")
async def task_events(task_id: str):
    async def gen():
        record = task_manager.get(task_id)
        if not record:
            yield {"event": "error", "data": "not_found"}
            return
        while True:
            msg = await record.queue.get()
            yield {"event": msg["type"], "data": json.dumps(msg)}
            if msg["type"] == "done":
                break
    return EventSourceResponse(gen())
```

### 3.8 阶段一验收（必须全部通过再继续）

```powershell
# 终端 1：启动 API
python -m imgbatch.api.main
# 应打印：IMG_BATCH_PORT=xxxxx

# 终端 2：测试（把 PORT 换成实际端口）
curl http://127.0.0.1:PORT/health
curl -X POST http://127.0.0.1:PORT/scan -H "Content-Type: application/json" -d "{\"folder\":\"C:\\\\test\",\"recursive\":true}"
```

写 `tests/test_api.py`：

- `test_health`
- `test_scan_empty_folder`
- `test_compress_task`（用 `tests/conftest.py` 的 `tmp_image_dir`）
- `test_task_cancel`

```powershell
python -m pytest tests/test_api.py -q
# 必须全绿
```

---

## 4. 阶段二：PyInstaller 打 sidecar

### 4.1 创建 `imgbatch-api.spec`

**关键：不要包含 tkinter**

```python
# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
ROOT = os.path.abspath('.')

hidden = collect_submodules('imgbatch')
hidden += ['uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
           'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
           'uvicorn.lifespan', 'uvicorn.lifespan.on', 'fastapi', 'sse_starlette']
# 显式排除 tkinter
excludes = ['tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy']

a = Analysis(
    ['imgbatch/api/main.py'],
    pathex=[ROOT],
    binaries=[],
    datas=[],
    hiddenimports=hidden,
    hookspath=[],
    excludes=excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='imgbatch-api',
    debug=False,
    console=True,          # 必须 console=True，Tauri 要读 stdout
    disable_windowed_traceback=False,
)
```

### 4.2 创建 `scripts/build-sidecar.ps1`

```powershell
$ErrorActionPreference = "Stop"
$Triple = "x86_64-pc-windows-msvc"   # Windows x64
$OutDir = "src-tauri/binaries"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
pyinstaller imgbatch-api.spec --noconfirm --clean
Copy-Item "dist/imgbatch-api.exe" "$OutDir/imgbatch-api-$Triple.exe" -Force
Write-Host "Sidecar -> $OutDir/imgbatch-api-$Triple.exe"
```

### 4.3 阶段二验收

```powershell
.\scripts\build-sidecar.ps1
.\src-tauri\binaries\imgbatch-api-x86_64-pc-windows-msvc.exe
# 必须看到 IMG_BATCH_PORT= 且 curl /health 成功
```

---

## 5. 阶段三：Tauri 2 壳

### 5.1 初始化（在项目根目录执行一次）

```powershell
npm create tauri-app@latest . -- --template react-ts
# 若冲突，改为在临时目录生成后把 src-tauri/ 移入
```

或手动创建 `src-tauri/`，`frontend/` 用 Vite 单独初始化。

### 5.2 `src-tauri/tauri.conf.json` 关键片段

```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "ImgBatch",
  "version": "3.0.0",
  "identifier": "com.imgbatch.app",
  "build": {
    "frontendDist": "../frontend/dist",
    "devUrl": "http://localhost:5173",
    "beforeDevCommand": "npm run dev --prefix ../frontend",
    "beforeBuildCommand": "npm run build --prefix ../frontend"
  },
  "app": {
    "windows": [{ "title": "ImgBatch", "width": 1000, "height": 820, "resizable": true }]
  },
  "bundle": {
    "active": true,
    "targets": ["nsis"],
    "externalBin": ["binaries/imgbatch-api"]
  }
}
```

### 5.3 `src-tauri/src/sidecar.rs`（核心逻辑）

**必须实现：**

1. `setup()` 时 `app.handle().shell().sidecar("imgbatch-api")` 启动
2. 读 stdout 每行，匹配 `IMG_BATCH_PORT=(\d+)`
3. 存入 `AppState { api_port: u16 }`
4. `on_window_event(CloseRequested)` 时 kill 子进程

参考 Tauri 2 文档：https://v2.tauri.app/develop/sidecar/

### 5.4 `src-tauri/src/commands.rs`（给前端的 Rust 命令）

| 命令名 | 参数 | 返回 | 用途 |
|--------|------|------|------|
| `get_api_base_url` | 无 | `"http://127.0.0.1:PORT"` | 前端拿 API 地址 |
| `pick_folder` | 无 | `Option<String>` | 选文件夹 |
| `pick_files` | 无 | `Vec<String>` | 多选图片 |
| `pick_save_file` | `default_name` | `Option<String>` | 另存为 |
| `open_path` | `path: String` | `()` | 资源管理器打开 |

**注册：** 在 `lib.rs` 的 `invoke_handler` 中 `generate_handler![get_api_base_url, pick_folder, ...]`。

### 5.5 阶段三验收

```powershell
# 先构建 sidecar
.\scripts\build-sidecar.ps1
# 开发模式
cd src-tauri
cargo tauri dev
```

打开应用后，浏览器控制台（F12）执行：

```javascript
const base = await window.__TAURI__.core.invoke('get_api_base_url');
fetch(base + '/health').then(r => r.json()).then(console.log);
// 应输出 {ok: true}
```

---

## 6. 阶段四：React 前端骨架（配合 UI UX Pro Max 技能）

### 6.0 前置：设计系统必须已生成

确认 `frontend/design-system/MASTER.md` 存在。若不存在，回到 **0.5.2** 执行 `search.py --persist`。

**AI 第一步：** 读取 `SKILL.md` + `MASTER.md`，将颜色/字体写入 `frontend/tailwind.config.js` 的 `theme.extend`：

```javascript
// frontend/tailwind.config.js 示例结构（具体色值从 MASTER.md 复制，禁止硬编码随机色）
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: 'var(--color-primary)',
        background: 'var(--color-background)',
        surface: 'var(--color-surface)',
        muted: 'var(--color-muted)',
        border: 'var(--color-border)',
      },
      fontFamily: {
        sans: ['var(--font-sans)'],
        mono: ['var(--font-mono)'],
      },
      borderRadius: {
        DEFAULT: 'var(--radius-md)',
      },
    },
  },
  plugins: [],
};
```

在 `frontend/src/styles/globals.css` 用 CSS 变量承接 MASTER.md 中的 token：

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  /* 以下数值必须从 design-system/MASTER.md 抄写 */
  --color-primary: #2563EB;
  --color-background: #F4F5F7;
  --color-surface: #FFFFFF;
  --color-muted: #656D76;
  --color-border: #D0D7DE;
  --font-sans: 'Inter', 'Segoe UI', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', Consolas, monospace;
  --radius-md: 8px;
}
```

### 6.1 初始化 frontend

```powershell
cd frontend
npm create vite@latest . -- --template react-ts
npm install zustand @tanstack/react-virtual react-i18next i18next lucide-react
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

可选（技能推荐 React 栈且 MASTER.md 指定时）：

```powershell
npx shadcn@latest init
# 按 MASTER.md 的圆角/主色配置 shadcn theme
```

### 6.1.1 用技能生成各页 override（建议 D3 完成）

```powershell
cd C:\Users\Administrator\Desktop\ImgBatch
$pages = @("workspace","compress","convert","rename","watermark","ai-rename","trim","inspect","normalize","spritesheet")
foreach ($p in $pages) {
  python .cursor/skills/ui-ux-pro-max/scripts/search.py "batch image $p settings" --design-system --persist -p "ImgBatch" --page $p --stack react
}
```

### 6.1.2 组件实现顺序（每步对照技能 checklist）

1. `TabLayout` + 侧栏/顶栏导航（参考 MASTER.md 的导航模式）
2. `FolderBar` — 主 CTA 用 primary 色，次要操作用 ghost/outline
3. `FileTable` — 数据密集表格：行高 40–48px、斑马纹可选、选中行 primary 浅色底
4. `FilterBar` — 水平工具栏，输入框统一高度 `h-9`
5. `PreviewPanel` — 卡片容器 `rounded-lg border shadow-sm`
6. `TaskProgress` — 贴底固定，进度条用 primary 色
7. `OutputOptions` — 单选+路径输入组合，与现 Tkinter 字段一致
8. 九个 `*Page.tsx` — **每页开始前读对应 `design-system/pages/*.md`**

### 6.1.3 向技能要 UI 时的标准 Prompt 模板

复制给 AI，替换 `[PageName]`：

```text
使用 UI UX Pro Max 技能，为 ImgBatch（桌面图片批处理工具）实现 [PageName] 页面。

约束：
- 阅读 frontend/design-system/MASTER.md 和 pages/[page-name].md
- React 18 + TypeScript + Tailwind，图标用 lucide-react
- 这是 Tauri 桌面应用，不是移动端；最小宽度 880px
- 不要 mock 业务逻辑，状态从 appStore 读取，操作调用 src/api/client.ts
- 字段必须与 docs/TAURI_MIGRATION.md 第 3.4 节 params 表一致

参照旧版行为：imgbatch/ui/app.py 中的 _tab_[xxx] 和 _run_[xxx]
```

### 6.2 `frontend/src/api/client.ts`

```typescript
import { invoke } from '@tauri-apps/api/core';

let cachedBase: string | null = null;

export async function getApiBase(): Promise<string> {
  if (!cachedBase) {
    cachedBase = await invoke<string>('get_api_base_url');
  }
  return cachedBase;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const base = await getApiBase();
  const res = await fetch(`${base}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
```

### 6.3 `frontend/src/api/sse.ts`

```typescript
export function subscribeTask(
  taskId: string,
  onProgress: (pct: number, message: string) => void,
  onDone: (status: string, result: unknown) => void,
): () => void {
  let closed = false;
  (async () => {
    const base = await getApiBase();
    const es = new EventSource(`${base}/tasks/${taskId}/events`);
    es.addEventListener('progress', (e) => {
      const d = JSON.parse(e.data);
      onProgress(d.pct, d.message);
    });
    es.addEventListener('done', (e) => {
      const d = JSON.parse(e.data);
      onDone(d.status, d.result);
      es.close();
    });
    es.onerror = () => { if (!closed) es.close(); };
  })();
  return () => { closed = true; };
}
```

### 6.4 `frontend/src/store/appStore.ts`（Zustand）

必须包含的状态：

```typescript
interface AppStore {
  folder: string;
  recursive: boolean;
  allFiles: FileInfo[];
  filteredFiles: FileInfo[];
  selectedFile: string | null;
  taskRunning: boolean;
  taskProgress: number;
  taskMessage: string;
  config: Record<string, unknown>;
  setFolder: (f: string) => void;
  refreshFiles: () => Promise<void>;
  applyFilter: () => Promise<void>;
  startTask: (type: string, params: Record<string, unknown>) => Promise<void>;
  cancelTask: () => Promise<void>;
}
```

`refreshFiles` 调用 `POST /scan` 再 `POST /filter`。

### 6.5 `App.tsx` 布局（照此结构写，样式遵循 design-system）

```
┌─────────────────────────────────────────────┐
│ FolderBar（路径 + 浏览 + 刷新 + 递归 + 语言）│  ← MASTER: header 区域
├─────────────────────────────────────────────┤
│ FilterBar                                    │  ← pages/workspace.md
├──────────────────────┬──────────────────────┤
│ FileTable            │ PreviewPanel         │
├──────────────────────┴──────────────────────┤
│ Tab 导航：9 个 Tab（图标+文字，Lucide）       │
│ [当前 Tab 对应的 Page 组件]                   │
├─────────────────────────────────────────────┤
│ TaskProgress（进度条 + 状态 + 取消）          │
└─────────────────────────────────────────────┘
```

**视觉要求（技能）：**

- 外层背景 `bg-background`，卡片/面板 `bg-surface border border-border rounded-lg`
- 主按钮 `bg-primary text-white hover:opacity-90 transition-colors duration-200`
- Tab 选中态：primary 色下划线或浅色底，与 Tkinter 版信息架构一致

### 6.6 i18n 迁移

1. 写脚本 `scripts/export_i18n.py`：读取 `imgbatch/infra/i18n.py` 的 `TRANSLATIONS`，输出 `frontend/src/i18n/zh.json` 和 `en.json`
2. 或手动复制 key（**key 名必须与 `tr('xxx')` 一致**）

### 6.7 阶段四验收

- [ ] `frontend/design-system/MASTER.md` 已提交到 git
- [ ] Tailwind 色值与 MASTER.md 一致（禁止魔法数散落各组件）
- [ ] 能选文件夹、显示文件列表
- [ ] 单击文件右侧出缩略图
- [ ] 压缩页能发起任务、进度条走动、完成后刷新列表
- [ ] 技能 Pre-delivery Checklist（0.5.4）抽检通过

---

## 7. 阶段五：逐页实现（每个 Page 的检查清单）

对 **每一个** Page，完成下列全部项才算 Done：

- [ ] 已读 `frontend/design-system/pages/[page].md`（若存在）
- [ ] UI 控件与现 Tkinter 页字段一一对应（对照 `imgbatch/ui/app.py` 中 `_tab_xxx`）
- [ ] 读取/写入 `config` 对应字段（见 `imgbatch/infra/settings.py` 的 `DEFAULT_CONFIG`）
- [ ] 点击「开始」调用 `POST /tasks`，`file_list` 来自 `filteredFiles.map(f => f.name)`
- [ ] `replace=false` 时必须校验 `out` 非空
- [ ] 错误用 toast 或 alert 展示 `result.errors`
- [ ] 手动测试：至少 1 张 PNG + 1 张 JPG

### 7.1 页面对照行号（AI 读代码用）

| Page | Tkinter 方法 | 运行方法 |
|------|-------------|----------|
| CompressPage | `_tab_compress` ~848 | `_run_compress` ~994 |
| ConvertPage | `_tab_convert` ~1036 | `_run_convert` ~1061 |
| RenamePage | `_tab_rename` ~1090 | `_run_rename` ~1159 |
| WatermarkPage | `_tab_watermark` ~1208 | `_run_watermark` ~1265 |
| AiRenamePage | `_tab_ai_rename` ~1325 | `_ai_analyze` / `_ai_apply` |
| TrimPage | `_tab_trim` ~1492 | `_run_trim` ~1501 |
| InspectPage | `_tab_inspect` ~1546 | `_run_inspect` ~1553 |
| NormalizePage | `_tab_normalize` ~1607 | `_run_normalize` ~1626 |
| SpritesheetPage | `_tab_spritesheet` ~1675 | `_run_spritesheet` ~1761 |

---

## 8. 阶段六：一键打包

### 8.1 `scripts/build-tauri.ps1`

```powershell
$ErrorActionPreference = "Stop"
.\scripts\build-sidecar.ps1
.\scripts\build-frontend.ps1   # npm run build
cd src-tauri
cargo tauri build
Write-Host "Installer in src-tauri/target/release/bundle/"
```

### 8.2 最终验收清单

- [ ] 未安装 Python 的机器可运行安装包
- [ ] 9 个 Tab 功能与旧版一致
- [ ] 撤销、备份管理可用
- [ ] 递归子目录 + 筛选 `> 1MB` 可压缩到输出目录
- [ ] 双击文件用系统看图打开（Tauri `open_path` 或 shell open）
- [ ] `pytest tests/` 全绿（含 `test_api.py`）
- [ ] 安装包体积 < 80MB

---

## 9. 阶段七：删除旧 UI

**仅在 8.2 全部通过后执行：**

```powershell
git rm image_compressor.pyw
git rm -r imgbatch/ui/
# 更新 README：启动方式改为 Tauri 安装包
# 更新 build.py 或标记 deprecated
```

新入口：Tauri 应用本身，不再有 `python image_compressor.pyw`。

---

## 10. 推送到远程

```powershell
git add .
git commit -m "feat: migrate GUI to Tauri + React + Python sidecar"
git push -u origin feat/tauri-react
# 若代理失败：
git -c http.proxy= -c https.proxy= push -u origin feat/tauri-react
```

创建 PR：`feat/tauri-react` → `main`，附测试说明。

---

## 11. 低级 AI 易犯错误（禁止）

| 错误 | 正确做法 |
|------|----------|
| 跳过 UI UX Pro Max 直接写界面 | 必须先 `--persist` 设计系统并读 MASTER.md |
| 在 React 里 `import Pillow` 或处理图片 | 全部走 Python API |
| 用 `Image.show()` 预览 | `POST /preview/thumb` 或 Tauri `open_path` |
| `file_list` 只传文件名不含子目录 | 必须用 `scan_folder` 返回的相对路径 `name` |
| 同时跑多个批处理任务 | `TaskManager` 只允许 1 个 |
| sidecar 用 `--windowed` | 必须 `console=True` |
| 忘记 `IMG_BATCH_PORT=` 打印 | Tauri 无法发现端口 |
| 在 API 线程直接调 `on_progress` 更新 FastAPI | 进度走 `queue` + SSE |
| 把 API key 写入 `config.json` | 仅内存传递；settings 里本就不存 key |
| 跳过测试直接打包 | 每阶段验收必须通过 |

---

## 12. 排错

| 现象 | 排查 |
|------|------|
| 前端 fetch 失败 | `get_api_base_url` 是否返回；sidecar 是否存活 |
| sidecar 闪退 | 命令行单独运行 exe 看 traceback |
| 压缩全部 source not found | `file_list` 路径是否为相对 `folder` 的路径 |
| SSE 无事件 | 检查 `EventSource` URL；CORS；任务是否已结束 |
| Tauri dev 白屏 | `beforeDevCommand` 是否启动 Vite；看终端报错 |
| 打包后找不到 sidecar | `externalBin` 名称与 `binaries/imgbatch-api-{triple}.exe` 是否匹配 |

---

## 13. 建议开发顺序（严格按天）

| 天 | 任务 | 产出 |
|----|------|------|
| D1 | 0.5 安装技能 + 生成 design-system + 3.1–3.8 API | MASTER.md + curl 可调 |
| D2 | 4 sidecar + 5 Tauri 壳 | `tauri dev` 通 health |
| D3 | 6 前端骨架 + 共享组件（按技能 checklist） | 能浏览文件 |
| D4 | Compress + Convert + TaskProgress | 核心闭环 |
| D5 | Rename + Watermark | |
| D6 | Trim + Inspect + Normalize | |
| D7 | AI Rename + Spritesheet | |
| D8 | 备份/撤销/i18n/拖拽 | |
| D9 | 打包 + 删旧 UI + PR | 安装包 |

---

## 14. 参考链接

- **UI UX Pro Max Skill:** https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- **技能 CLI:** `npm install -g ui-ux-pro-max-cli` → `uipro init --ai cursor`
- Tauri 2 Sidecar: https://v2.tauri.app/develop/sidecar/
- Tauri 2 Commands: https://v2.tauri.app/develop/calling-rust/
- FastAPI: https://fastapi.tiangolo.com/
- SSE Starlette: https://github.com/sysid/sse-starlette

---

**文档版本：** 1.1  
**最后更新：** 2026-07-15  
**UI 技能：** [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)（前端强制）  
**维护：** 下次开发从 **0.5 安装技能** 或 **阶段一 3.1** 开始（若技能与设计系统已就绪则直接从阶段一）。
