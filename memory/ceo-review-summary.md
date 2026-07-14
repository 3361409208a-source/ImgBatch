# CEO Review Summary — ImgBatch

**日期:** 2026-07-14
**模式:** SELECTIVE EXPANSION
**方案:** B — 渐进式模块化
**状态:** DONE

---

## 最强挑战 (Top 3 Issues)

1. **单体单类 2374 行** — 所有业务逻辑、UI、线程、动画、AI 调用耦合在一个 `ImgBatchApp` 类中，零可测试性，任何修改高回归风险
2. **线程管理完全无序** — 无取消机制、无超时、`is_running` 竞态条件，线程崩溃后应用永久锁定
3. **零测试 + 零日志 + 零设置持久化** — 不可验证、不可诊断、不可恢复，用户每次启动重新配置全部参数

---

## 基线修复清单 (Bulletproof Baseline)

| # | 修复项 | 严重度 | 优先级 |
|---|--------|--------|--------|
| 1 | 业务逻辑与 UI 分离（第一优先级） | 高 | P0 |
| 2 | 语言切换改为文本更新，不销毁重建标签页 | 高 | P1 |
| 3 | 线程管理：取消机制 + ThreadPoolExecutor + 锁保护 | 高 | P1 |
| 4 | 移除/整合 4 个孤儿脚本（检查独特逻辑→整合→删除） | 中 | P2 |
| 5 | 全部通用 except Exception 替换为具体异常 + 结构化日志 | 高 | P1 |
| 6 | 工作线程用 try/finally 保证 is_running 重置 | 高 | P1 |
| 7 | 压缩预估按格式分组采样 | 中 | P2 |
| 8 | 重命名添加冲突检测 + 用户选择（跳过/覆盖/自动序号） | 高 | P1 |
| 9 | 操作运行时禁用相关控件 | 中 | P2 |
| 10 | 统一 i18n：所有硬编码文本移入 TRANSLATIONS + _t() 调用 | 中 | P2 |
| 11 | 中文变量名 `个错误` 改为 `errors`（6 处） | 中 | P2 |
| 12 | 提取公共方法消除 DRY 违规（备份/RGBA转换/线程骨架/inspect action） | 中 | P2 |
| 13 | 核心层单元测试，目标覆盖率 > 80% | 高 | P1 |
| 14 | 引入 logging 模块 + 文件日志（~/.imgbatch/imgbatch.log） | 高 | P1 |
| 15 | 引入 config.json 设置持久化 | 高 | P1 |
| 16 | DeepSeek API：重试 + 响应验证 + 分批发送 + token 追踪 | 中高 | P2 |
| 17 | _refresh() 移到工作线程 + 尺寸延迟加载 | 中高 | P2 |
| 18 | 统一 UX：按钮文案一致 + 空/加载/错误状态处理一致 | 低 | P3 |

---

## 扩展机会 (All Accepted)

| # | 扩展项 | 工作量 | 依赖 |
|---|--------|--------|------|
| 1 | CLI 命令行接口 + agent skill | S | 核心逻辑分离 |
| 2 | 操作历史与撤销系统（Ctrl+Z） | M | 设置持久化 |
| 3 | 操作进度 ETA 估算 | S | 线程管理 |
| 4 | 压缩前后对比预览（左右分栏/滑动对比） | M | 预览面板重构 |
| 5 | 递归子目录扫描 | S | _refresh 重构 |
| 6 | 自定义水印预设保存 | S | 设置持久化 |
| 7 | 批量操作队列（多操作排序依次执行） | M | 核心逻辑分离 |
| 8 | EXIF 元数据保留/清除选项 | S | 核心逻辑分离 |

---

## 延迟处理 (Deferred)

| 项目 | 原因 |
|------|------|
| API Key 安全（keyring 存储 + 错误消息过滤 + 数据上传提示） | 模块化完成后处理 |
| 路径遍历防护 | 本地桌面工具风险低，暂不处理 |
| 水印 resize 缓存 | 性能影响低，暂不处理 |

---

## NOT in scope (Explicitly Excluded)

- 插件/扩展系统（桌面工具过度工程化）
- 跨平台支持（Windows-only by design）
- 完整架构重建（选择渐进式方案 B）
- 主题重新设计（XP Classic 是风格选择）

---

## 推荐路径 (Recommended Path)

### 阶段 1: 基础分离 (P0)
- 将 `image_compressor.pyw` 拆分为模块化结构
- 核心层无 GUI 依赖，可独立测试
- 引入 logging + config.json

### 阶段 2: 安全加固 (P1)
- 线程管理重构（取消/池/锁）
- 异常处理全面替换
- 重命名冲突检测
- 测试骨架搭建

### 阶段 3: 功能扩展 (P2)
- CLI 接口 + agent skill
- 操作历史与撤销
- ETA 估算
- 对比预览
- 递归扫描
- 水印预设
- 操作队列
- EXIF 选项

### 阶段 4: 打磨 (P3)
- UX 统一
- i18n 完整化
- API Key 安全加固

---

## 目标模块结构

```
ImgBatch/
├── imgbatch/                  # 核心包
│   ├── __init__.py
│   ├── core/                  # 无 GUI 依赖的业务逻辑
│   │   ├── __init__.py
│   │   ├── compress.py        # 压缩逻辑
│   │   ├── convert.py         # 格式转换
│   │   ├── rename.py          # 重命名（含冲突检测）
│   │   ├── watermark.py       # 水印
│   │   ├── trim.py            # 裁剪透明
│   │   ├── normalize.py       # 规范化
│   │   ├── inspect.py         # 检查
│   │   └── ai_rename.py       # AI 重命名（DeepSeek 集成）
│   ├── ui/                    # tkinter UI 层
│   │   ├── __init__.py
│   │   ├── app.py             # 主应用窗口
│   │   ├── tabs/              # 各标签页
│   │   │   ├── compress.py
│   │   │   ├── convert.py
│   │   │   ├── rename.py
│   │   │   ├── watermark.py
│   │   │   ├── ai_rename.py
│   │   │   ├── trim.py
│   │   │   ├── inspect.py
│   │   │   └── normalize.py
│   │   ├── widgets/           # 可复用控件
│   │   └── theme.py           # 主题配色
│   ├── infra/                 # 基础设施
│   │   ├── __init__.py
│   │   ├── logger.py          # 日志系统
│   │   ├── settings.py        # 设置持久化
│   │   ├── threading.py       # 线程管理（取消/池/锁）
│   │   └── i18n.py            # 国际化
│   ├── cli/                   # 命令行接口
│   │   ├── __init__.py
│   │   └── main.py
│   └── history.py             # 操作历史与撤销
├── tests/                     # 测试
│   ├── conftest.py
│   ├── fixtures/              # 测试图片
│   ├── test_compress.py
│   ├── test_convert.py
│   ├── test_rename.py
│   ├── test_watermark.py
│   ├── test_trim.py
│   ├── test_normalize.py
│   ├── test_ai_rename.py
│   └── test_settings.py
├── skills/                    # Agent skill
│   └── imgbatch-cli/
│       └── SKILL.md
├── image_compressor.pyw       # 向后兼容入口（导入 imgbatch.ui.app）
├── build.py                   # 打包脚本（更新）
├── README.md
└── memory/
    └── ceo-review-summary.md  # 本文件
```

  target_file: c:\Users\Administrator\Desktop\ImgBatch\memory\ceo-review-summary.md
  code_edit: # CEO Review Summary — ImgBatch

**日期:** 2026-07-14
**模式:** SELECTIVE EXPANSION
**方案:** B — 渐进式模块化
**状态:** DONE

---

## 最强挑战 (Top 3 Issues)

1. **单体单类 2374 行** — 所有业务逻辑、UI、线程、动画、AI 调用耦合在一个 `ImgBatchApp` 类中，零可测试性，任何修改高回归风险
2. **线程管理完全无序** — 无取消机制、无超时、`is_running` 竞态条件，线程崩溃后应用永久锁定
3. **零测试 + 零日志 + 零设置持久化** — 不可验证、不可诊断、不可恢复，用户每次启动重新配置全部参数

---

## 基线修复清单 (Bulletproof Baseline)

| # | 修复项 | 严重度 | 优先级 |
|---|--------|--------|--------|
| 1 | 业务逻辑与 UI 分离（第一优先级） | 高 | P0 |
| 2 | 语言切换改为文本更新，不销毁重建标签页 | 高 | P1 |
| 3 | 线程管理：取消机制 + ThreadPoolExecutor + 锁保护 | 高 | P1 |
| 4 | 移除/整合 4 个孤儿脚本（检查独特逻辑→整合→删除） | 中 | P2 |
| 5 | 全部通用 except Exception 替换为具体异常 + 结构化日志 | 高 | P1 |
| 6 | 工作线程用 try/finally 保证 is_running 重置 | 高 | P1 |
| 7 | 压缩预估按格式分组采样 | 中 | P2 |
| 8 | 重命名添加冲突检测 + 用户选择（跳过/覆盖/自动序号） | 高 | P1 |
| 9 | 操作运行时禁用相关控件 | 中 | P2 |
| 10 | 统一 i18n：所有硬编码文本移入 TRANSLATIONS + _t() 调用 | 中 | P2 |
| 11 | 中文变量名 `个错误` 改为 `errors`（6 处） | 中 | P2 |
| 12 | 提取公共方法消除 DRY 违规（备份/RGBA转换/线程骨架/inspect action） | 中 | P2 |
| 13 | 核心层单元测试，目标覆盖率 > 80% | 高 | P1 |
| 14 | 引入 logging 模块 + 文件日志（~/.imgbatch/imgbatch.log） | 高 | P1 |
| 15 | 引入 config.json 设置持久化 | 高 | P1 |
| 16 | DeepSeek API：重试 + 响应验证 + 分批发送 + token 追踪 | 中高 | P2 |
| 17 | _refresh() 移到工作线程 + 尺寸延迟加载 | 中高 | P2 |
| 18 | 统一 UX：按钮文案一致 + 空/加载/错误状态处理一致 | 低 | P3 |

---

## 扩展机会 (All Accepted)

| # | 扩展项 | 工作量 | 依赖 |
|---|--------|--------|------|
| 1 | CLI 命令行接口 + agent skill | S | 核心逻辑分离 |
| 2 | 操作历史与撤销系统（Ctrl+Z） | M | 设置持久化 |
| 3 | 操作进度 ETA 估算 | S | 线程管理 |
| 4 | 压缩前后对比预览（左右分栏/滑动对比） | M | 预览面板重构 |
| 5 | 递归子目录扫描 | S | _refresh 重构 |
| 6 | 自定义水印预设保存 | S | 设置持久化 |
| 7 | 批量操作队列（多操作排序依次执行） | M | 核心逻辑分离 |
| 8 | EXIF 元数据保留/清除选项 | S | 核心逻辑分离 |

---

## 延迟处理 (Deferred)

| 项目 | 原因 |
|------|------|
| API Key 安全（keyring 存储 + 错误消息过滤 + 数据上传提示） | 模块化完成后处理 |
| 路径遍历防护 | 本地桌面工具风险低，暂不处理 |
| 水印 resize 缓存 | 性能影响低，暂不处理 |

---

## NOT in scope (Explicitly Excluded)

- 插件/扩展系统（桌面工具过度工程化）
- 跨平台支持（Windows-only by design）
- 完整架构重建（选择渐进式方案 B）
- 主题重新设计（XP Classic 是风格选择）

---

## 推荐路径 (Recommended Path)

### 阶段 1: 基础分离 (P0)
- 将 `image_compressor.pyw` 拆分为模块化结构
- 核心层无 GUI 依赖，可独立测试
- 引入 logging + config.json

### 阶段 2: 安全加固 (P1)
- 线程管理重构（取消/池/锁）
- 异常处理全面替换
- 重命名冲突检测
- 测试骨架搭建

### 阶段 3: 功能扩展 (P2)
- CLI 接口 + agent skill
- 操作历史与撤销
- ETA 估算
- 对比预览
- 递归扫描
- 水印预设
- 操作队列
- EXIF 选项

### 阶段 4: 打磨 (P3)
- UX 统一
- i18n 完整化
- API Key 安全加固

---

## 目标模块结构

```
ImgBatch/
├── imgbatch/                  # 核心包
│   ├── __init__.py
│   ├── core/                  # 无 GUI 依赖的业务逻辑
│   │   ├── __init__.py
│   │   ├── compress.py        # 压缩逻辑
│   │   ├── convert.py         # 格式转换
│   │   ├── rename.py          # 重命名（含冲突检测）
│   │   ├── watermark.py       # 水印
│   │   ├── trim.py            # 裁剪透明
│   │   ├── normalize.py       # 规范化
│   │   ├── inspect.py         # 检查
│   │   └── ai_rename.py       # AI 重命名（DeepSeek 集成）
│   ├── ui/                    # tkinter UI 层
│   │   ├── __init__.py
│   │   ├── app.py             # 主应用窗口
│   │   ├── tabs/              # 各标签页
│   │   │   ├── compress.py
│   │   │   ├── convert.py
│   │   │   ├── rename.py
│   │   │   ├── watermark.py
│   │   │   ├── ai_rename.py
│   │   │   ├── trim.py
│   │   │   ├── inspect.py
│   │   │   └── normalize.py
│   │   ├── widgets/           # 可复用控件
│   │   └── theme.py           # 主题配色
│   ├── infra/                 # 基础设施
│   │   ├── __init__.py
│   │   ├── logger.py          # 日志系统
│   │   ├── settings.py        # 设置持久化
│   │   ├── threading.py       # 线程管理（取消/池/锁）
│   │   └── i18n.py            # 国际化
│   ├── cli/                   # 命令行接口
│   │   ├── __init__.py
│   │   └── main.py
│   └── history.py             # 操作历史与撤销
├── tests/                     # 测试
│   ├── conftest.py
│   ├── fixtures/              # 测试图片
│   ├── test_compress.py
│   ├── test_convert.py
│   ├── test_rename.py
│   ├── test_watermark.py
│   ├── test_trim.py
│   ├── test_normalize.py
│   ├── test_ai_rename.py
│   └── test_settings.py
├── skills/                    # Agent skill
│   └── imgbatch-cli/
│       └── SKILL.md
├── image_compressor.pyw       # 向后兼容入口（导入 imgbatch.ui.app）
├── build.py                   # 打包脚本（更新）
├── README.md
└── memory/
    └── ceo-review-summary.md  # 本文件
```

