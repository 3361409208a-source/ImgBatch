export const SITE = {
  name: 'ImgBatch',
  tagline: '全能图片批处理工具箱',
  taglineEn: 'All-in-One Batch Image Toolkit',
  version: '3.0.0',
  github: 'https://github.com/3361409208a-source/ImgBatch',
  releases: 'https://github.com/3361409208a-source/ImgBatch/releases/latest',
  license: 'MIT',
} as const;

export const NAV = [
  { id: 'features', label: '功能' },
  { id: 'desktop', label: '桌面体验' },
  { id: 'how', label: '使用方式' },
  { id: 'download', label: '下载' },
] as const;

export const FEATURES = [
  {
    icon: 'compress',
    title: '压缩',
    titleEn: 'Compress',
    desc: '质量与缩放无级调节，EXIF 保留/清除，实时大小预估，支持备份与批量输出。',
  },
  {
    icon: 'convert',
    title: '格式转换',
    titleEn: 'Convert',
    desc: 'JPG、PNG、WEBP、BMP、TIFF、GIF、ICO 互转，智能处理透明度与动图。',
  },
  {
    icon: 'rename',
    title: '批量重命名',
    titleEn: 'Rename',
    desc: '前缀后缀、查找替换、序号模板，冲突检测与实时预览。',
  },
  {
    icon: 'watermark',
    title: '水印',
    titleEn: 'Watermark',
    desc: '文字或图片水印，自定义位置、透明度与缩放比例。',
  },
  {
    icon: 'ai',
    title: 'AI 智能重命名',
    titleEn: 'AI Rename',
    desc: 'DeepSeek 一键分析；无 Key 时可用秘塔 AI 助手，自动填入需求并解析 JSON 结果。',
  },
  {
    icon: 'trim',
    title: '裁剪透明',
    titleEn: 'Trim Alpha',
    desc: '裁剪 PNG 透明边距，可自定义 padding，适合图标与素材整理。',
  },
  {
    icon: 'inspect',
    title: '图片检查',
    titleEn: 'Inspect',
    desc: '分析 PNG 画布与内容尺寸、四周边距，批量结果一目了然。',
  },
  {
    icon: 'normalize',
    title: '规范化',
    titleEn: 'Normalize',
    desc: 'Alpha 阈值裁剪、统一高度缩放、均匀透明边距，适合标题图规格统一。',
  },
  {
    icon: 'spritesheet',
    title: '精灵图',
    titleEn: 'Sprite Sheet',
    desc: '多图智能排列合并，支持间距、2 的幂次画布与 JSON 坐标导出。',
  },
  {
    icon: 'gif',
    title: 'GIF 编辑',
    titleEn: 'GIF Edit',
    desc: '动图优化、缩放、减色、变速、倒放、裁透明边、水印与拆帧导出。',
  },
] as const;

export const CONTEXT_MENU_ITEMS = [
  '压缩',
  '格式转换',
  '重命名',
  '水印',
  '裁边',
  '规范化',
  '检查',
  'GIF 动图',
] as const;

export const DESKTOP_HIGHLIGHTS = [
  {
    icon: 'desktop',
    title: '原生桌面应用',
    desc: 'Tauri 2 + React 现代界面，Python 本地处理核心，Windows 安装包一键部署。',
  },
  {
    icon: 'context',
    title: '资源管理器右键',
    desc: '八大功能各自独立菜单项（ImgBatch 压缩 / 转换 / 重命名…），每项展开即见全部子选项。',
  },
  {
    icon: 'quick',
    title: '快捷弹窗',
    desc: '右键触发精简弹窗，预填文件与动作参数，改几个选项即可一键执行。',
  },
  {
    icon: 'ai',
    title: '秘塔 AI 助手',
    desc: 'AI 重命名无需 API Key：打开 metaso.cn 自动填入命名需求，粘贴 JSON 即可预览并应用。',
  },
  {
    icon: 'backup',
    title: '安全与可撤销',
    desc: '自动备份、操作撤销、结构化日志，批量处理更放心。',
  },
] as const;

export const STEPS = [
  {
    step: '01',
    title: '下载安装',
    desc: '获取 Windows 安装包并完成安装。安装程序会自动注册资源管理器右键菜单。',
  },
  {
    step: '02',
    title: '选择文件',
    desc: '打开主窗口加载文件夹，或在资源管理器中选中图片后使用 ImgBatch 右键菜单。',
  },
  {
    step: '03',
    title: '配置并执行',
    desc: '主界面精细调节，或快捷弹窗使用预设；AI 重命名支持 DeepSeek 与秘塔两种方式。',
  },
] as const;

export const STATS = [
  { value: '10', label: '核心模块' },
  { value: '7+', label: '图片格式' },
  { value: '100%', label: '本地处理' },
] as const;
