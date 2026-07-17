import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Play, X, FolderOpen, Trash2 } from 'lucide-react';
import { api } from '../api/client';
import { subscribeTask } from '../api/sse';
import type { FileInfo } from '../api/types';
import {
  FALLBACK_CONVERT_CATALOG,
  IMAGE_INPUT_EXT,
  targetSupportsQuality,
  type ConvertCatalog,
} from '../utils/convertFormats';

const IMAGE_EXT = IMAGE_INPUT_EXT;

const ACTION_META: Record<
  string,
  { label: string; hint: string; accent: string; height: number }
> = {
  compress: {
    label: '压缩',
    hint: '调整画质与尺寸，减小文件体积',
    accent: '#0F766E',
    height: 640,
  },
  convert: {
    label: '格式转换',
    hint: '批量转换图片格式',
    accent: '#0369A1',
    height: 560,
  },
  rename: {
    label: '重命名',
    hint: '按规则批量重命名文件',
    accent: '#7C3AED',
    height: 600,
  },
  watermark: {
    label: '水印',
    hint: '为图片添加文字水印',
    accent: '#C2410C',
    height: 660,
  },
  trim: {
    label: '裁边',
    hint: '裁剪透明边缘并保留边距',
    accent: '#B45309',
    height: 560,
  },
  normalize: {
    label: '规范化',
    hint: '统一高度与透明裁切参数',
    accent: '#0E7490',
    height: 620,
  },
  inspect: {
    label: '图片检查',
    hint: '分析 PNG 画布、内容区域与四边留白',
    accent: '#475569',
    height: 520,
  },
  gif: {
    label: 'GIF 动图',
    hint: '优化、缩放、拆帧等动图编辑',
    accent: '#BE185D',
    height: 520,
  },
};

const POSITIONS = [
  { v: 'top-left', t: '左上' },
  { v: 'top-right', t: '右上' },
  { v: 'center', t: '居中' },
  { v: 'bottom-left', t: '左下' },
  { v: 'bottom-right', t: '右下' },
];

interface InspectRow {
  name: string;
  canvas: string;
  content: string;
  left_pad: string;
  right_pad: string;
  top_pad: string;
  bot_pad: string;
}

interface LaunchPayload {
  quickAction?: string | null;
  paths?: string[];
  out?: string | null;
  targetFmt?: string | null;
  quality?: number | null;
  resizePct?: number | null;
  padding?: number | null;
  targetHeight?: number | null;
  renameMode?: string | null;
  wmPosition?: string | null;
  wmText?: string | null;
  autoRun?: boolean | null;
  gifMode?: string | null;
  speedFactor?: number | null;
}

function normalizeTargetFmt(fmt: string): string {
  const t = fmt.trim().toLowerCase();
  if (!t) return '.png';
  return t.startsWith('.') ? t : `.${t}`;
}

function extOf(path: string): string {
  const i = path.lastIndexOf('.');
  return i >= 0 ? path.slice(i).toLowerCase() : '';
}

function baseName(path: string): string {
  const parts = path.replace(/\\/g, '/').split('/');
  return parts[parts.length - 1] || path;
}

function parentDir(path: string): string {
  const cleaned = path.replace(/[/\\]+$/, '');
  const i = Math.max(cleaned.lastIndexOf('\\'), cleaned.lastIndexOf('/'));
  if (i <= 0) return cleaned;
  return cleaned.slice(0, i);
}

function isImagePath(path: string): boolean {
  return IMAGE_EXT.has(extOf(path));
}

function looksLikeFile(path: string): boolean {
  const e = extOf(path);
  return e.length > 0 && e.length <= 5;
}

async function resolveTargets(paths: string[]): Promise<{ folder: string; files: FileInfo[]; skipped: number }> {
  const filePaths: string[] = [];
  const dirPaths: string[] = [];

  for (const p of paths) {
    if (looksLikeFile(p)) filePaths.push(p);
    else dirPaths.push(p);
  }

  let folder = '';
  let files: FileInfo[] = [];
  let skipped = 0;

  if (dirPaths.length > 0) {
    folder = dirPaths[0].replace(/[/\\]+$/, '');
    try {
      const res = await api.scan(folder, true);
      files = res.files.filter((f) => isImagePath(f.path) || isImagePath(f.name));
    } catch {
      files = [];
    }
  }

  if (filePaths.length > 0) {
    const byFolder = new Map<string, string[]>();
    for (const p of filePaths) {
      const dir = parentDir(p);
      if (!byFolder.has(dir)) byFolder.set(dir, []);
      byFolder.get(dir)!.push(p);
    }
    let bestDir = '';
    let bestList: string[] = [];
    for (const [dir, list] of byFolder) {
      if (list.length > bestList.length) {
        bestDir = dir;
        bestList = list;
      }
    }
    for (const [dir, list] of byFolder) {
      if (dir !== bestDir) skipped += list.length;
    }
    folder = bestDir || folder;
    const mapped: FileInfo[] = bestList.map((p) => ({
      name: baseName(p),
      path: p,
      size: 0,
      size_str: '',
      dimensions: '',
      format: extOf(p).replace('.', '').toUpperCase() || '?',
    }));
    if (files.length && folder === bestDir) {
      const names = new Set(mapped.map((f) => f.name));
      files = [...mapped, ...files.filter((f) => !names.has(f.name))];
    } else if (!dirPaths.length || folder === bestDir) {
      files = mapped.length ? mapped : files;
    } else {
      files = mapped;
    }
  }

  return { folder, files, skipped };
}

async function enrichViaProbe(files: FileInfo[]): Promise<FileInfo[]> {
  if (files.length === 0) return files;
  try {
    const res = await api.probe(files.map((f) => f.path));
    const byPath = new Map(res.files.map((f) => [f.path.toLowerCase(), f]));
    return files.map((f) => byPath.get(f.path.toLowerCase()) || f);
  } catch {
    return files;
  }
}

async function enrichFromScan(folder: string, files: FileInfo[]): Promise<FileInfo[]> {
  if (!folder || files.length === 0) return files;
  try {
    const res = await api.scan(folder, false);
    const byName = new Map(res.files.map((f) => [f.name.toLowerCase(), f]));
    return files.map((f) => byName.get(f.name.toLowerCase()) || f);
  } catch {
    return files;
  }
}

async function revealQuickWindow() {
  try {
    const { invoke } = await import('@tauri-apps/api/core');
    await invoke('quick_window_ready');
  } catch {
    /* browser / non-tauri */
  }
}

async function syncWindowChrome(action: string, resultCount = 0) {
  const meta = ACTION_META[action] || ACTION_META.compress;
  let h = meta.height;
  let w = 440;
  if (action === 'inspect' && resultCount > 0) {
    w = 480;
    h = resultCount === 1 ? 520 : Math.min(720, 420 + resultCount * 36);
  }
  try {
    const { getCurrentWindow } = await import('@tauri-apps/api/window');
    const { LogicalSize } = await import('@tauri-apps/api/dpi');
    const win = getCurrentWindow();
    await win.setTitle(`ImgBatch · ${meta.label}`);
    await win.setSize(new LogicalSize(w, h));
  } catch {
    /* browser / non-tauri */
  }
}

function InspectResultCard({ row }: { row: InspectRow }) {
  return (
    <div className="rounded-md border border-border bg-white/70 p-3 space-y-2 text-xs">
      <div className="font-mono font-medium truncate" title={row.name}>
        {row.name}
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div className="rounded border border-border/70 px-2 py-1.5 bg-[color:var(--color-muted)]/20">
          <div className="text-[10px] text-[color:var(--color-muted-fg)]">画布 Canvas</div>
          <div className="font-mono text-sm mt-0.5">{row.canvas}</div>
        </div>
        <div className="rounded border border-border/70 px-2 py-1.5 bg-[color:var(--color-muted)]/20">
          <div className="text-[10px] text-[color:var(--color-muted-fg)]">内容 Content</div>
          <div className="font-mono text-sm mt-0.5">{row.content}</div>
        </div>
        <div className="rounded border border-border/70 px-2 py-1.5 bg-[color:var(--color-muted)]/20">
          <div className="text-[10px] text-[color:var(--color-muted-fg)]">左留白 L</div>
          <div className="font-mono text-sm mt-0.5">{row.left_pad}</div>
        </div>
        <div className="rounded border border-border/70 px-2 py-1.5 bg-[color:var(--color-muted)]/20">
          <div className="text-[10px] text-[color:var(--color-muted-fg)]">右留白 R</div>
          <div className="font-mono text-sm mt-0.5">{row.right_pad}</div>
        </div>
        <div className="rounded border border-border/70 px-2 py-1.5 bg-[color:var(--color-muted)]/20">
          <div className="text-[10px] text-[color:var(--color-muted-fg)]">上留白 T</div>
          <div className="font-mono text-sm mt-0.5">{row.top_pad}</div>
        </div>
        <div className="rounded border border-border/70 px-2 py-1.5 bg-[color:var(--color-muted)]/20">
          <div className="text-[10px] text-[color:var(--color-muted-fg)]">下留白 B</div>
          <div className="font-mono text-sm mt-0.5">{row.bot_pad}</div>
        </div>
      </div>
    </div>
  );
}

export function QuickActionPage() {
  const [action, setAction] = useState('compress');
  const [folder, setFolder] = useState('');
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [skipped, setSkipped] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [doneMsg, setDoneMsg] = useState('');
  const [inspectRows, setInspectRows] = useState<InspectRow[]>([]);

  const [quality, setQuality] = useState(75);
  const [resizePct, setResizePct] = useState(100);
  const [exifMode, setExifMode] = useState('keep');
  const [targetFmt, setTargetFmt] = useState('.png');
  const [renameMode, setRenameMode] = useState('prefix');
  const [renamePrefix, setRenamePrefix] = useState('img_');
  const [renameSuffix, setRenameSuffix] = useState('');
  const [renameFind, setRenameFind] = useState('');
  const [renameReplace, setRenameReplace] = useState('');
  const [wmText, setWmText] = useState('水印');
  const [wmOpacity, setWmOpacity] = useState(50);
  const [wmPosition, setWmPosition] = useState('bottom-right');
  const [wmSize, setWmSize] = useState(36);
  const [padding, setPadding] = useState(4);
  const [alphaThreshold, setAlphaThreshold] = useState(28);
  const [targetHeight, setTargetHeight] = useState(280);
  const [normPadding, setNormPadding] = useState(6);
  const [replace, setReplace] = useState(true);
  const [doBackup, setDoBackup] = useState(true);
  const [out, setOut] = useState('');
  const [presetConvertFmt, setPresetConvertFmt] = useState<string | null>(null);
  const [convertCatalog, setConvertCatalog] = useState<ConvertCatalog>(FALLBACK_CONVERT_CATALOG);
  const [gifMode, setGifMode] = useState('optimize');
  const [speedFactor, setSpeedFactor] = useState(2);

  const autoRunRef = useRef(false);
  const meta = ACTION_META[action] || ACTION_META.compress;

  const applyPayload = useCallback(async (payload: LaunchPayload) => {
    setLoading(true);
    setError('');
    setDoneMsg('');
    setInspectRows([]);
    autoRunRef.current = false;
    const act = (payload.quickAction || 'compress').toLowerCase();
    setAction(act);
    void syncWindowChrome(act);
    if (payload.out) setOut(payload.out);
    if (payload.quality != null) setQuality(payload.quality);
    else if (act === 'convert') setQuality(85);
    if (payload.resizePct != null) setResizePct(payload.resizePct);
    if (payload.padding != null) setPadding(payload.padding);
    if (payload.targetHeight != null) setTargetHeight(payload.targetHeight);
    if (payload.renameMode) setRenameMode(payload.renameMode);
    if (payload.wmPosition) setWmPosition(payload.wmPosition);
    if (payload.wmText) setWmText(payload.wmText);
    if (payload.gifMode) setGifMode(payload.gifMode);
    if (payload.speedFactor != null) setSpeedFactor(payload.speedFactor);
    if (payload.targetFmt) {
      const fmt = normalizeTargetFmt(payload.targetFmt);
      setTargetFmt(fmt);
      if (act === 'convert') {
        setPresetConvertFmt(fmt);
      } else {
        setPresetConvertFmt(null);
      }
    } else {
      setPresetConvertFmt(null);
    }
    if (payload.autoRun) autoRunRef.current = true;
    if (act === 'convert' && payload.autoRun) autoRunRef.current = true;
    const paths = payload.paths || [];
    if (paths.length === 0) {
      setFiles([]);
      setFolder('');
      setError('未收到文件路径');
      setLoading(false);
      return;
    }
    try {
      const resolved = await resolveTargets(paths);
      const useProbe = resolved.files.length > 0 && resolved.files.every((f) => looksLikeFile(f.path));
      const enriched = useProbe
        ? await enrichViaProbe(resolved.files)
        : await enrichFromScan(resolved.folder, resolved.files);
      setFolder(resolved.folder);
      setFiles(enriched);
      setSkipped(resolved.skipped);
      if (enriched.length === 0) {
        setError('没有可处理的图片文件');
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
      void revealQuickWindow();
    }
  }, []);

  useEffect(() => {
    void api.convertFormats().then(setConvertCatalog).catch(() => {});
  }, []);

  useEffect(() => {
    let unlisten: (() => void) | undefined;
    (async () => {
      try {
        const { invoke } = await import('@tauri-apps/api/core');
        const { listen } = await import('@tauri-apps/api/event');
        const payload = await invoke<LaunchPayload>('get_launch_payload');
        await applyPayload(payload);
        unlisten = await listen<LaunchPayload>('quick-action', (ev) => {
          void applyPayload(ev.payload);
        });
      } catch (e) {
        setError(String(e));
        setLoading(false);
        void revealQuickWindow();
      }
    })();
    return () => {
      unlisten?.();
    };
  }, [applyPayload]);

  const imageFiles = useMemo(
    () => files.filter((f) => isImagePath(f.path) || isImagePath(f.name)),
    [files],
  );

  const pngFiles = useMemo(
    () => imageFiles.filter((f) => extOf(f.name) === '.png' || extOf(f.path) === '.png'),
    [imageFiles],
  );

  const inspectTargets = useMemo(() => {
    if (action === 'inspect') return pngFiles;
    if (action === 'gif') {
      return imageFiles.filter((f) => extOf(f.name) === '.gif' || extOf(f.path) === '.gif');
    }
    return imageFiles;
  }, [action, pngFiles, imageFiles]);

  const removeFile = (path: string) => {
    setFiles((prev) => prev.filter((f) => f.path !== path && f.name !== path));
  };

  const pickOut = async () => {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const path = await invoke<string | null>('pick_folder');
      if (path) setOut(path);
    } catch {
      /* ignore */
    }
  };

  const needsOutputOpts = action !== 'inspect' && action !== 'rename';

  const buildParams = (): Record<string, unknown> => {
    const outVal = replace ? null : out || null;
    switch (action) {
      case 'compress':
        return {
          quality,
          resize_pct: resizePct,
          do_backup: doBackup,
          replace,
          out: outVal,
          exif_mode: exifMode,
        };
      case 'convert':
        return {
          target_fmt: targetFmt,
          quality: targetSupportsQuality(convertCatalog, targetFmt) ? quality : undefined,
          do_backup: doBackup,
          replace,
          out: outVal,
        };
      case 'rename':
        return {
          mode: renameMode,
          prefix: renamePrefix,
          suffix: renameSuffix || '_bak',
          find: renameFind,
          replace: renameReplace,
          seq_template: 'photo_{num}',
          seq_start: 1,
          seq_digits: 3,
          lowercase: renameMode === 'lowercase',
          uppercase: renameMode === 'uppercase',
        };
      case 'watermark':
        return {
          params: {
            type: 'text',
            text: wmText,
            fontsize: wmSize,
            opacity: wmOpacity / 100,
            position: wmPosition,
            color: '#ffffff',
            image_path: '',
            img_scale: 0.2,
          },
          do_backup: doBackup,
          replace,
          out: outVal,
        };
      case 'trim':
        return { padding, do_backup: doBackup, replace, out: outVal };
      case 'normalize':
        return {
          alpha_threshold: alphaThreshold,
          target_height: targetHeight,
          padding: normPadding,
          do_backup: doBackup,
          replace,
          out: outVal,
        };
      case 'inspect':
        return {};
      case 'gif': {
        const base: Record<string, unknown> = {
          mode: gifMode,
          do_backup: doBackup,
          replace,
          out: outVal,
          resize_pct: resizePct,
          speed_factor: gifMode === 'speed' ? speedFactor : undefined,
          colors: gifMode === 'reduce_colors' ? 128 : 256,
          optimize: true,
        };
        if (gifMode === 'watermark') {
          base.watermark = {
            type: 'text',
            text: wmText,
            opacity: wmOpacity / 100,
            position: wmPosition,
          };
        }
        return base;
      }
      default:
        return {};
    }
  };

  const handleStart = async () => {
    setError('');
    setDoneMsg('');
    setInspectRows([]);
    if (!folder) {
      setError('缺少工作目录');
      return;
    }
    if (inspectTargets.length === 0) {
      setError(action === 'inspect' ? '没有可检查的 PNG 文件（检查仅支持 .png）' : '没有可处理的图片');
      return;
    }
    if (needsOutputOpts && !replace && !out.trim()) {
      setError('未勾选覆盖原图时，请设置输出目录');
      return;
    }

    setRunning(true);
    setProgress(0);
    setMessage('启动中…');
    const taskType = action === 'gif' ? 'gif_edit' : action;
    try {
      const res = await api.createTask({
        type: taskType,
        folder,
        file_list: inspectTargets.map((f) => f.name),
        params: buildParams(),
      });
      subscribeTask(
        res.task_id,
        (pct, msg) => {
          setProgress(pct);
          setMessage(msg);
        },
        (status, result) => {
          setRunning(false);
          if (status === 'error') {
            setError(typeof result === 'string' ? result : JSON.stringify(result));
            setProgress(0);
          } else if (status === 'cancelled') {
            setMessage('已取消');
          } else {
            setProgress(100);
            setDoneMsg(`完成：${inspectTargets.length} 个文件`);
            setMessage('');
            if (action === 'inspect' && result && typeof result === 'object') {
              const payload = result as { results?: InspectRow[] };
              if (Array.isArray(payload.results)) {
                setInspectRows(payload.results);
                void syncWindowChrome(action, payload.results.length);
              }
            }
          }
        },
      );
    } catch (e) {
      setRunning(false);
      setError(String(e));
    }
  };

  useEffect(() => {
    if (!autoRunRef.current || loading || running) return;
    if (!folder || inspectTargets.length === 0) return;
    autoRunRef.current = false;
    void handleStart();
  }, [loading, running, action, folder, inspectTargets.length]);

  const handleClose = async () => {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('close_quick_session');
    } catch {
      try {
        const { getCurrentWindow } = await import('@tauri-apps/api/window');
        await getCurrentWindow().close();
      } catch {
        window.close();
      }
    }
  };

  const openOut = async () => {
    const target = needsOutputOpts && !replace && out ? out : folder;
    if (!target) return;
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('open_path', { path: target });
    } catch {
      /* ignore */
    }
  };

  const startLabel =
    action === 'inspect' ? '开始检查' : action === 'rename' ? '开始重命名' : `开始${meta.label.replace(/^图片/, '')}`;

  const canStart = !running && !loading && inspectTargets.length > 0;
  const inspectDone = action === 'inspect' && inspectRows.length > 0;

  return (
    <div className="flex flex-col h-screen bg-surface text-foreground">
      <header
        className="px-4 py-3 border-b border-border flex items-center justify-between shrink-0"
        style={{ borderTop: `3px solid ${meta.accent}` }}
      >
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span
              className="text-[10px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded text-white shrink-0"
              style={{ background: meta.accent }}
            >
              {meta.label}
            </span>
            <div className="text-sm font-semibold tracking-tight truncate">ImgBatch 快捷操作</div>
          </div>
          <div className="text-[11px] text-[color:var(--color-muted-fg)] mt-1 truncate">{meta.hint}</div>
        </div>
        <button type="button" className="btn-ghost h-8 w-8 p-0 justify-center" onClick={() => void handleClose()} title="关闭">
          <X size={16} />
        </button>
      </header>

      <div className="flex-1 overflow-auto px-4 py-3 flex flex-col gap-3 min-h-0">
        {loading && <p className="text-sm text-[color:var(--color-muted-fg)]">加载中…</p>}

        {!loading && (
          <>
            <div className="text-xs text-[color:var(--color-muted-fg)] truncate" title={folder}>
              目录：{folder || '—'}
            </div>
            {skipped > 0 && (
              <p className="text-xs text-amber-700">另有 {skipped} 个文件不在同一目录，已忽略</p>
            )}

            <div className="border border-border rounded-md overflow-hidden shrink-0 max-h-[120px] flex flex-col">
              <div className="px-2 py-1.5 text-[11px] border-b border-border" style={{ background: `${meta.accent}14` }}>
                {action === 'inspect' ? `待检查 PNG (${pngFiles.length})` : `文件 (${imageFiles.length})`}
              </div>
              <ul className="overflow-auto text-xs flex-1">
                {(action === 'inspect' ? pngFiles : imageFiles).map((f) => (
                  <li
                    key={f.path || f.name}
                    className="flex items-center gap-2 px-2 py-1.5 border-b border-border/60 last:border-0"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-mono" title={f.path}>
                        {f.name}
                      </div>
                      {(f.dimensions || f.size_str || f.format) && (
                        <div className="text-[10px] text-[color:var(--color-muted-fg)] truncate">
                          {[f.format, f.dimensions, f.size_str].filter(Boolean).join(' · ')}
                        </div>
                      )}
                    </div>
                    <button
                      type="button"
                      className="btn-ghost h-6 w-6 p-0 justify-center shrink-0"
                      onClick={() => removeFile(f.path || f.name)}
                      title="移除"
                    >
                      <Trash2 size={12} />
                    </button>
                  </li>
                ))}
                {(action === 'inspect' ? pngFiles : imageFiles).length === 0 && (
                  <li className="px-2 py-3 text-[color:var(--color-muted-fg)]">
                    {action === 'inspect' ? '无 PNG 文件' : '无图片文件'}
                  </li>
                )}
              </ul>
            </div>

            {action === 'inspect' && imageFiles.length > pngFiles.length && (
              <p className="text-xs text-amber-700">
                已忽略 {imageFiles.length - pngFiles.length} 个非 PNG 文件（检查仅支持 PNG）
              </p>
            )}

            {!inspectDone && !(presetConvertFmt && action === 'convert') && (
            <div className="flex flex-col gap-2.5 rounded-md border border-border p-3 bg-[color:var(--color-muted)]/20 shrink-0">
              <div className="text-[11px] font-medium" style={{ color: meta.accent }}>
                {meta.label}选项
              </div>

              {action === 'inspect' ? (
                <p className="text-xs text-[color:var(--color-muted-fg)] leading-relaxed">
                  将分析每张 PNG 的透明区域与内容边界，输出画布、内容区域与四边留白。
                </p>
              ) : (
              <>
              {action === 'compress' && (
                <>
                  <label className="flex flex-col gap-1">
                    <span className="label-muted">质量 {quality}</span>
                    <input type="range" min={1} max={100} value={quality} onChange={(e) => setQuality(Number(e.target.value))} />
                  </label>
                  <label className="flex flex-col gap-1">
                    <span className="label-muted">缩放 {resizePct}%</span>
                    <input type="range" min={10} max={100} value={resizePct} onChange={(e) => setResizePct(Number(e.target.value))} />
                  </label>
                  <label className="flex flex-col gap-1">
                    <span className="label-muted">EXIF</span>
                    <select className="field" value={exifMode} onChange={(e) => setExifMode(e.target.value)}>
                      <option value="keep">保留</option>
                      <option value="strip">清除</option>
                      <option value="orientation">仅方向</option>
                    </select>
                  </label>
                </>
              )}

              {action === 'convert' && (
                <>
                  <label className="flex flex-col gap-1">
                    <span className="label-muted">目标格式</span>
                    <select className="field" value={targetFmt} onChange={(e) => setTargetFmt(e.target.value)}>
                      {convertCatalog.targets.map((f) => (
                        <option key={f.ext} value={f.ext}>{f.ext}</option>
                      ))}
                    </select>
                  </label>
                  {targetSupportsQuality(convertCatalog, targetFmt) && (
                    <label className="flex flex-col gap-1">
                      <span className="label-muted">质量 {quality}</span>
                      <input type="range" min={1} max={100} value={quality} onChange={(e) => setQuality(Number(e.target.value))} />
                    </label>
                  )}
                </>
              )}

              {action === 'rename' && (
                <>
                  <label className="flex flex-col gap-1">
                    <span className="label-muted">模式</span>
                    <select className="field" value={renameMode} onChange={(e) => setRenameMode(e.target.value)}>
                      <option value="prefix">添加前缀</option>
                      <option value="suffix">添加后缀</option>
                      <option value="replace">查找替换</option>
                      <option value="seq">序号</option>
                    </select>
                  </label>
                  {(renameMode === 'prefix' || renameMode === 'seq') && (
                    <label className="flex flex-col gap-1">
                      <span className="label-muted">前缀</span>
                      <input className="field" value={renamePrefix} onChange={(e) => setRenamePrefix(e.target.value)} />
                    </label>
                  )}
                  {renameMode === 'suffix' && (
                    <label className="flex flex-col gap-1">
                      <span className="label-muted">后缀</span>
                      <input className="field" value={renameSuffix} onChange={(e) => setRenameSuffix(e.target.value)} />
                    </label>
                  )}
                  {renameMode === 'replace' && (
                    <>
                      <label className="flex flex-col gap-1">
                        <span className="label-muted">查找</span>
                        <input className="field" value={renameFind} onChange={(e) => setRenameFind(e.target.value)} />
                      </label>
                      <label className="flex flex-col gap-1">
                        <span className="label-muted">替换为</span>
                        <input className="field" value={renameReplace} onChange={(e) => setRenameReplace(e.target.value)} />
                      </label>
                    </>
                  )}
                </>
              )}

              {action === 'watermark' && (
                <>
                  <label className="flex flex-col gap-1">
                    <span className="label-muted">水印文字</span>
                    <input className="field" value={wmText} onChange={(e) => setWmText(e.target.value)} />
                  </label>
                  <label className="flex flex-col gap-1">
                    <span className="label-muted">字号 {wmSize}</span>
                    <input type="range" min={12} max={96} value={wmSize} onChange={(e) => setWmSize(Number(e.target.value))} />
                  </label>
                  <label className="flex flex-col gap-1">
                    <span className="label-muted">透明度 {wmOpacity}%</span>
                    <input type="range" min={5} max={100} value={wmOpacity} onChange={(e) => setWmOpacity(Number(e.target.value))} />
                  </label>
                  <label className="flex flex-col gap-1">
                    <span className="label-muted">位置</span>
                    <select className="field" value={wmPosition} onChange={(e) => setWmPosition(e.target.value)}>
                      {POSITIONS.map((p) => (
                        <option key={p.v} value={p.v}>{p.t}</option>
                      ))}
                    </select>
                  </label>
                </>
              )}

              {action === 'trim' && (
                <label className="flex flex-col gap-1">
                  <span className="label-muted">保留边距 (px)</span>
                  <input className="field" type="number" min={0} value={padding} onChange={(e) => setPadding(Number(e.target.value))} />
                </label>
              )}

              {action === 'normalize' && (
                <>
                  <label className="flex flex-col gap-1">
                    <span className="label-muted">透明阈值</span>
                    <input className="field" type="number" min={0} max={255} value={alphaThreshold} onChange={(e) => setAlphaThreshold(Number(e.target.value))} />
                  </label>
                  <label className="flex flex-col gap-1">
                    <span className="label-muted">目标高度</span>
                    <input className="field" type="number" min={1} value={targetHeight} onChange={(e) => setTargetHeight(Number(e.target.value))} />
                  </label>
                  <label className="flex flex-col gap-1">
                    <span className="label-muted">边距</span>
                    <input className="field" type="number" min={0} value={normPadding} onChange={(e) => setNormPadding(Number(e.target.value))} />
                  </label>
                </>
              )}

              {needsOutputOpts && (
                <div className="flex flex-col gap-2 pt-1 border-t border-border/70">
                  <label className="flex items-center gap-2 text-xs">
                    <input type="checkbox" checked={replace} onChange={(e) => setReplace(e.target.checked)} />
                    覆盖原图
                  </label>
                  <label className="flex items-center gap-2 text-xs">
                    <input type="checkbox" checked={doBackup} onChange={(e) => setDoBackup(e.target.checked)} />
                    操作前备份
                  </label>
                  {!replace && (
                    <div className="flex gap-1.5 items-center">
                      <input
                        className="field flex-1 text-xs"
                        placeholder="输出目录"
                        value={out}
                        onChange={(e) => setOut(e.target.value)}
                      />
                      <button type="button" className="btn-ghost h-8" onClick={() => void pickOut()}>
                        <FolderOpen size={14} />
                      </button>
                    </div>
                  )}
                </div>
              )}
              </>
              )}
            </div>
            )}

            {running && (
              <div className="flex flex-col gap-1">
                <div className="h-1.5 rounded bg-[color:var(--color-muted)] overflow-hidden">
                  <div className="h-full transition-all" style={{ width: `${Math.min(100, progress)}%`, background: meta.accent }} />
                </div>
                <p className="text-[11px] text-[color:var(--color-muted-fg)] truncate">{message}</p>
              </div>
            )}

            {error && <p className="text-xs text-red-600 whitespace-pre-wrap">{error}</p>}
            {presetConvertFmt && action === 'convert' && !running && !doneMsg && (
              <p className="text-xs text-[color:var(--color-muted-fg)]">
                目标格式：<span className="font-mono font-medium text-foreground">{presetConvertFmt}</span>，正在开始转换…
              </p>
            )}

            {doneMsg && !inspectDone && <p className="text-xs" style={{ color: meta.accent }}>{doneMsg}</p>}

            {inspectDone && (
              <div className="flex flex-col gap-2 shrink-0">
                <div className="text-xs font-medium" style={{ color: meta.accent }}>
                  检查结果（{inspectRows.length}）
                </div>
                {inspectRows.length === 1 ? (
                  <InspectResultCard row={inspectRows[0]} />
                ) : (
                  <div className="overflow-auto border border-border rounded-md max-h-64">
                    <table className="w-full text-xs font-mono border-collapse">
                      <thead className="sticky top-0 bg-[color:var(--color-muted)]/80">
                        <tr className="text-[color:var(--color-muted-fg)]">
                          <th className="px-2 py-2 text-left">文件名</th>
                          <th className="px-2 py-2">画布</th>
                          <th className="px-2 py-2">内容</th>
                          <th className="px-2 py-2">L</th>
                          <th className="px-2 py-2">R</th>
                          <th className="px-2 py-2">T</th>
                          <th className="px-2 py-2">B</th>
                        </tr>
                      </thead>
                      <tbody>
                        {inspectRows.map((r, i) => (
                          <tr key={`${r.name}-${i}`} className="border-t border-border/70">
                            <td className="px-2 py-2 align-middle max-w-[100px] truncate" title={r.name}>{r.name}</td>
                            <td className="px-2 py-2 align-middle text-center whitespace-nowrap">{r.canvas}</td>
                            <td className="px-2 py-2 align-middle text-center whitespace-nowrap">{r.content}</td>
                            <td className="px-2 py-2 align-middle text-center">{r.left_pad}</td>
                            <td className="px-2 py-2 align-middle text-center">{r.right_pad}</td>
                            <td className="px-2 py-2 align-middle text-center">{r.top_pad}</td>
                            <td className="px-2 py-2 align-middle text-center">{r.bot_pad}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      <footer className="px-4 py-3 border-t border-border flex gap-2 shrink-0">
        {doneMsg ? (
          <>
            {action !== 'inspect' && (
              <button type="button" className="btn-secondary flex-1" onClick={() => void openOut()}>
                打开目录
              </button>
            )}
            <button type="button" className="btn-primary flex-1" onClick={() => void handleClose()}>
              关闭
            </button>
          </>
        ) : (
          <>
            <button type="button" className="btn-ghost flex-1" onClick={() => void handleClose()} disabled={running}>
              取消
            </button>
            <button
              type="button"
              className="btn-primary flex-1"
              style={{ background: meta.accent }}
              disabled={!canStart}
              onClick={() => void handleStart()}
            >
              <Play size={14} />
              {startLabel}
            </button>
          </>
        )}
      </footer>
    </div>
  );
}
