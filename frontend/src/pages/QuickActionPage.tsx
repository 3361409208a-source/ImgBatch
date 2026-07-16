import { useCallback, useEffect, useMemo, useState } from 'react';
import { Play, X, FolderOpen, Trash2 } from 'lucide-react';
import { api } from '../api/client';
import { subscribeTask } from '../api/sse';
import type { FileInfo } from '../api/types';

const IMAGE_EXT = new Set([
  '.png',
  '.jpg',
  '.jpeg',
  '.webp',
  '.gif',
  '.bmp',
  '.tif',
  '.tiff',
  '.ico',
]);

const ACTION_LABELS: Record<string, string> = {
  compress: '压缩',
  convert: '格式转换',
  rename: '重命名',
  watermark: '水印',
  trim: '裁边',
  normalize: '规范化',
  inspect: '检查',
};

interface LaunchPayload {
  quickAction?: string | null;
  paths?: string[];
  out?: string | null;
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

  // Options
  const [quality, setQuality] = useState(75);
  const [targetFmt, setTargetFmt] = useState('.png');
  const [renamePrefix, setRenamePrefix] = useState('img_');
  const [wmText, setWmText] = useState('水印');
  const [padding, setPadding] = useState(4);
  const [replace, setReplace] = useState(true);
  const [doBackup, setDoBackup] = useState(true);
  const [out, setOut] = useState('');

  const applyPayload = useCallback(async (payload: LaunchPayload) => {
    setLoading(true);
    setError('');
    setDoneMsg('');
    const act = (payload.quickAction || 'compress').toLowerCase();
    setAction(act);
    if (payload.out) setOut(payload.out);
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
      setFolder(resolved.folder);
      setFiles(resolved.files);
      setSkipped(resolved.skipped);
      if (resolved.files.length === 0) {
        setError('没有可处理的图片文件');
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
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

  const buildParams = (): Record<string, unknown> => {
    const outVal = replace ? null : out || null;
    switch (action) {
      case 'compress':
        return {
          quality,
          resize_pct: 100,
          do_backup: doBackup,
          replace,
          out: outVal,
          exif_mode: 'keep',
        };
      case 'convert':
        return { target_fmt: targetFmt, do_backup: doBackup, replace, out: outVal };
      case 'rename':
        return {
          mode: 'prefix',
          prefix: renamePrefix,
          suffix: '',
          find: '',
          replace: '',
          seq_template: 'photo_{num}',
          seq_start: 1,
          seq_digits: 3,
          lowercase: false,
          uppercase: false,
        };
      case 'watermark':
        return {
          params: {
            type: 'text',
            text: wmText,
            fontsize: 36,
            opacity: 0.5,
            position: 'bottom-right',
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
          alpha_threshold: 28,
          target_height: 280,
          padding: 6,
          do_backup: doBackup,
          replace,
          out: outVal,
        };
      case 'inspect':
        return {};
      default:
        return {};
    }
  };

  const handleStart = async () => {
    setError('');
    setDoneMsg('');
    if (!folder) {
      setError('缺少工作目录');
      return;
    }
    const list = action === 'inspect' || action === 'rename' ? imageFiles : imageFiles;
    if (list.length === 0) {
      setError('没有可处理的图片');
      return;
    }
    if (!replace && action !== 'inspect' && action !== 'rename' && !out.trim()) {
      setError('未勾选覆盖原图时，请设置输出目录');
      return;
    }

    setRunning(true);
    setProgress(0);
    setMessage('启动中…');
    try {
      const res = await api.createTask({
        type: action,
        folder,
        file_list: list.map((f) => f.name),
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
            setDoneMsg(`完成：${list.length} 个文件`);
            setMessage('');
          }
        },
      );
    } catch (e) {
      setRunning(false);
      setError(String(e));
    }
  };

  const handleClose = async () => {
    try {
      const { getCurrentWindow } = await import('@tauri-apps/api/window');
      await getCurrentWindow().close();
    } catch {
      window.close();
    }
  };

  const openOut = async () => {
    const target = !replace && out ? out : folder;
    if (!target) return;
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('open_path', { path: target });
    } catch {
      /* ignore */
    }
  };

  const title = ACTION_LABELS[action] || action;

  return (
    <div className="flex flex-col h-screen bg-surface text-foreground">
      <header className="px-4 py-3 border-b border-border flex items-center justify-between shrink-0">
        <div>
          <div className="text-sm font-semibold tracking-tight">ImgBatch 快捷操作</div>
          <div className="text-xs text-[color:var(--color-muted-fg)] mt-0.5">{title}</div>
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

            <div className="border border-border rounded-md overflow-hidden flex-1 min-h-[120px] max-h-[180px] flex flex-col">
              <div className="px-2 py-1.5 text-[11px] bg-[color:var(--color-muted)]/40 border-b border-border">
                文件 ({imageFiles.length})
              </div>
              <ul className="overflow-auto text-xs flex-1">
                {imageFiles.map((f) => (
                  <li
                    key={f.path || f.name}
                    className="flex items-center gap-1 px-2 py-1 border-b border-border/60 last:border-0"
                  >
                    <span className="truncate flex-1 font-mono" title={f.path}>
                      {f.name}
                    </span>
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
                {imageFiles.length === 0 && (
                  <li className="px-2 py-3 text-[color:var(--color-muted-fg)]">无图片文件</li>
                )}
              </ul>
            </div>

            {/* Minimal options */}
            <div className="flex flex-col gap-2.5">
              {action === 'compress' && (
                <label className="flex flex-col gap-1">
                  <span className="label-muted">质量 {quality}</span>
                  <input
                    type="range"
                    min={1}
                    max={100}
                    value={quality}
                    onChange={(e) => setQuality(Number(e.target.value))}
                  />
                </label>
              )}
              {action === 'convert' && (
                <label className="flex flex-col gap-1">
                  <span className="label-muted">目标格式</span>
                  <select
                    className="field"
                    value={targetFmt}
                    onChange={(e) => setTargetFmt(e.target.value)}
                  >
                    {['.png', '.jpg', '.webp', '.bmp', '.gif'].map((f) => (
                      <option key={f} value={f}>
                        {f}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              {action === 'rename' && (
                <label className="flex flex-col gap-1">
                  <span className="label-muted">前缀</span>
                  <input
                    className="field"
                    value={renamePrefix}
                    onChange={(e) => setRenamePrefix(e.target.value)}
                  />
                </label>
              )}
              {action === 'watermark' && (
                <label className="flex flex-col gap-1">
                  <span className="label-muted">水印文字</span>
                  <input className="field" value={wmText} onChange={(e) => setWmText(e.target.value)} />
                </label>
              )}
              {action === 'trim' && (
                <label className="flex flex-col gap-1">
                  <span className="label-muted">边距</span>
                  <input
                    className="field"
                    type="number"
                    min={0}
                    value={padding}
                    onChange={(e) => setPadding(Number(e.target.value))}
                  />
                </label>
              )}

              {action !== 'inspect' && action !== 'rename' && (
                <>
                  <label className="flex items-center gap-2 text-xs">
                    <input
                      type="checkbox"
                      checked={replace}
                      onChange={(e) => setReplace(e.target.checked)}
                    />
                    覆盖原图
                  </label>
                  <label className="flex items-center gap-2 text-xs">
                    <input
                      type="checkbox"
                      checked={doBackup}
                      onChange={(e) => setDoBackup(e.target.checked)}
                    />
                    备份
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
                </>
              )}
            </div>

            {running && (
              <div className="flex flex-col gap-1">
                <div className="h-1.5 rounded bg-[color:var(--color-muted)] overflow-hidden">
                  <div
                    className="h-full bg-[color:var(--color-primary)] transition-all"
                    style={{ width: `${Math.min(100, progress)}%` }}
                  />
                </div>
                <p className="text-[11px] text-[color:var(--color-muted-fg)] truncate">{message}</p>
              </div>
            )}

            {error && <p className="text-xs text-red-600 whitespace-pre-wrap">{error}</p>}
            {doneMsg && <p className="text-xs text-teal-800">{doneMsg}</p>}
          </>
        )}
      </div>

      <footer className="px-4 py-3 border-t border-border flex gap-2 shrink-0">
        {doneMsg ? (
          <>
            <button type="button" className="btn-secondary flex-1" onClick={() => void openOut()}>
              打开目录
            </button>
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
              disabled={running || loading || imageFiles.length === 0}
              onClick={() => void handleStart()}
            >
              <Play size={14} />
              开始
            </button>
          </>
        )}
      </footer>
    </div>
  );
}
