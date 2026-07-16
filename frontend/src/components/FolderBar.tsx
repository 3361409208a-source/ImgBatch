import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FolderOpen, RefreshCw, Languages, Archive } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { BackupManager } from './BackupManager';

const ICON = { size: 15, strokeWidth: 1.5 } as const;

export function FolderBar() {
  const { t } = useTranslation();
  const {
    folder,
    recursive,
    language,
    setFolder,
    setRecursive,
    refreshFiles,
    setLanguage,
    setStatusMessage,
    statusMessage,
  } = useAppStore();
  const [backupOpen, setBackupOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  const handleBrowse = async () => {
    if (busy) return;
    setBusy(true);
    setStatusMessage('');
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const path = await invoke<string | null>('pick_folder');
      if (!path) {
        setStatusMessage('已取消选择');
        return;
      }
      setFolder(path);
      setStatusMessage('正在扫描…');
      await refreshFiles();
      const n = useAppStore.getState().allFiles.length;
      setStatusMessage(n > 0 ? `已加载 ${n} 个文件` : '该文件夹下没有图片（可勾选「包含子目录」）');
    } catch (e) {
      console.error('pick_folder failed', e);
      setStatusMessage(`选择文件夹失败: ${e}`);
      const path = window.prompt('选择失败，请手动输入文件夹路径:');
      if (path) {
        setFolder(path);
        await refreshFiles();
      }
    } finally {
      setBusy(false);
    }
  };

  const handleRefresh = async () => {
    if (!folder) {
      setStatusMessage('请先选择文件夹');
      return;
    }
    setBusy(true);
    try {
      setStatusMessage('正在扫描…');
      await refreshFiles();
      const n = useAppStore.getState().allFiles.length;
      const err = useAppStore.getState().taskError;
      if (err) setStatusMessage(err);
      else setStatusMessage(n > 0 ? `已加载 ${n} 个文件` : '该文件夹下没有图片（可勾选「包含子目录」）');
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <header className="flex items-center gap-3 px-4 py-2.5 panel border-x-0 border-t-0 shadow-sm">
        <div className="flex items-center gap-2.5 shrink-0 pr-3 border-r border-border">
          <div className="flex h-7 min-w-7 px-1.5 items-center justify-center rounded-md bg-primary text-on-primary text-[10px] font-bold tracking-wide">
            IB
          </div>
          <span className="text-sm font-semibold tracking-tight text-foreground">ImgBatch</span>
        </div>

        <button
          type="button"
          onClick={() => void handleBrowse()}
          disabled={busy}
          className="btn-primary shrink-0 gap-1.5 disabled:opacity-50"
        >
          <FolderOpen {...ICON} className="shrink-0" />
          <span>{t('browse')}</span>
        </button>

        <input
          type="text"
          value={folder}
          onChange={(e) => setFolder(e.target.value)}
          onBlur={() => {
            if (folder) void handleRefresh();
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && folder) void handleRefresh();
          }}
          placeholder={t('target_folder')}
          className="field flex-1 font-mono text-xs min-w-0"
        />

        <label className="flex items-center gap-1.5 text-[13px] text-[color:var(--color-muted-fg)] cursor-pointer select-none shrink-0">
          <input
            type="checkbox"
            checked={recursive}
            onChange={(e) => {
              setRecursive(e.target.checked);
              if (folder) {
                setTimeout(() => void handleRefresh(), 0);
              }
            }}
          />
          {t('recursive_scan')}
        </label>

        <div className="flex items-center gap-1.5 shrink-0">
          <button
            type="button"
            onClick={() => void handleRefresh()}
            disabled={busy}
            className="btn-outline disabled:opacity-50"
            title={t('refresh')}
          >
            <RefreshCw {...ICON} className={`shrink-0 ${busy ? 'animate-spin' : ''}`} />
            <span>{t('refresh')}</span>
          </button>
          <button type="button" onClick={() => setBackupOpen(true)} className="btn-outline" title={t('backup_mgr')}>
            <Archive {...ICON} className="shrink-0" />
            <span>{t('backup_mgr')}</span>
          </button>
          <button
            type="button"
            onClick={() => setLanguage(language === 'zh' ? 'en' : 'zh')}
            className="btn-ghost px-2"
            title="Language"
          >
            <Languages {...ICON} className="shrink-0" />
            <span className="text-xs font-semibold">{language === 'zh' ? '\u4e2d' : 'EN'}</span>
          </button>
        </div>
      </header>
      {statusMessage ? (
        <div className="px-4 py-1 text-[11px] bg-[color:var(--color-surface-2)] border-b border-border text-[color:var(--color-muted-fg)] truncate">
          {statusMessage}
        </div>
      ) : null}
      <BackupManager open={backupOpen} onClose={() => setBackupOpen(false)} />
    </>
  );
}
