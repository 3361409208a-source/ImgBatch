import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FolderOpen, ImagePlus, FileText, RefreshCw, Languages, Archive, X, Settings } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { BackupManager } from './BackupManager';
import { SettingsModal } from './SettingsModal';

const ICON = { size: 15, strokeWidth: 1.5 } as const;

export function FolderBar() {
  const { t } = useTranslation();
  const {
    folder,
    recursive,
    language,
    targetMode,
    scanKind,
    setFolder,
    setRecursive,
    refreshFiles,
    loadPinnedFiles,
    clearPinnedMode,
    setLanguage,
    setStatusMessage,
    statusMessage,
  } = useAppStore();
  const [backupOpen, setBackupOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const isDoc = scanKind === 'document';

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
      setStatusMessage(
        n > 0
          ? `已加载 ${n} 个文件`
          : isDoc
            ? '该文件夹下没有文档（可勾选「包含子目录」）'
            : '该文件夹下没有图片（可勾选「包含子目录」）',
      );
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

  const handleOpenFiles = async () => {
    if (busy) return;
    setBusy(true);
    setStatusMessage('');
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const paths = await invoke<string[]>('pick_files', { kind: scanKind });
      if (!paths || paths.length === 0) {
        setStatusMessage('已取消选择');
        return;
      }
      await loadPinnedFiles(paths);
    } catch (e) {
      console.error('pick_files failed', e);
      setStatusMessage(`${isDoc ? '选择文档' : '选择图片'}失败: ${e}`);
    } finally {
      setBusy(false);
    }
  };

  const handleClearPinned = async () => {
    setBusy(true);
    try {
      await clearPinnedMode();
    } finally {
      setBusy(false);
    }
  };

  const handleRefresh = async () => {
    if (!folder && targetMode === 'folder') {
      setStatusMessage(t('select_folder_first'));
      return;
    }
    setBusy(true);
    try {
      setStatusMessage('正在扫描…');
      await refreshFiles();
      const n = useAppStore.getState().allFiles.length;
      const err = useAppStore.getState().taskError;
      if (err) setStatusMessage(err);
      else if (useAppStore.getState().targetMode !== 'folder') {
        /* status set by loadPinnedFiles */
      } else {
        setStatusMessage(
          n > 0
            ? `已加载 ${n} 个文件`
            : isDoc
              ? '该文件夹下没有文档（可勾选「包含子目录」）'
              : '该文件夹下没有图片（可勾选「包含子目录」）',
        );
      }
    } finally {
      setBusy(false);
    }
  };

  const modeLabel = (() => {
    if (targetMode === 'single') return isDoc ? t('mode_single_doc') : t('mode_single');
    if (targetMode === 'multi') return isDoc ? t('mode_multi_doc') : t('mode_multi');
    return isDoc ? t('mode_document') : t('mode_folder');
  })();

  const openLabel = isDoc ? t('open_document') : t('open_image');
  const OpenIcon = isDoc ? FileText : ImagePlus;
  const clearLabel =
    targetMode === 'single'
      ? isDoc
        ? t('clear_single_doc')
        : t('clear_single')
      : isDoc
        ? t('clear_multi_doc')
        : t('clear_multi');

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

        <button
          type="button"
          onClick={() => void handleOpenFiles()}
          disabled={busy}
          className="btn-outline shrink-0 gap-1.5 disabled:opacity-50"
          title={openLabel}
        >
          <OpenIcon {...ICON} className="shrink-0" />
          <span>{openLabel}</span>
        </button>

        <input
          type="text"
          value={folder}
          onChange={(e) => setFolder(e.target.value)}
          onBlur={() => {
            if (folder && targetMode === 'folder') void handleRefresh();
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && folder && targetMode === 'folder') void handleRefresh();
          }}
          placeholder={isDoc ? t('target_folder_doc') : t('target_folder')}
          className="field flex-1 font-mono text-xs min-w-0"
        />

        <span
          className={`shrink-0 rounded-md px-2 py-1 text-[11px] font-medium ${
            targetMode === 'folder' && !isDoc
              ? 'bg-[color:var(--color-surface-2)] text-[color:var(--color-muted-fg)]'
              : 'bg-primary/15 text-primary'
          }`}
        >
          {modeLabel}
        </span>

        {targetMode !== 'folder' && (
          <button
            type="button"
            onClick={() => void handleClearPinned()}
            disabled={busy}
            className="btn-ghost shrink-0 gap-1 px-2 text-[12px] disabled:opacity-50"
            title={clearLabel}
          >
            <X {...ICON} className="shrink-0" />
            <span>{clearLabel}</span>
          </button>
        )}

        <label className="flex items-center gap-1.5 text-[13px] text-[color:var(--color-muted-fg)] cursor-pointer select-none shrink-0">
          <input
            type="checkbox"
            checked={recursive}
            disabled={targetMode !== 'folder'}
            onChange={(e) => {
              setRecursive(e.target.checked);
              if (folder && targetMode === 'folder') {
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
          <button type="button" onClick={() => setSettingsOpen(true)} className="btn-outline text-primary border-primary/30 bg-primary/5 hover:bg-primary/10" title={t('settings')}>
            <Settings {...ICON} className="shrink-0" />
            <span>{t('settings')}</span>
          </button>
        </div>
      </header>
      {statusMessage ? (
        <div className="px-4 py-1 text-[11px] bg-[color:var(--color-surface-2)] border-b border-border text-[color:var(--color-muted-fg)] truncate">
          {statusMessage}
        </div>
      ) : null}
      <BackupManager open={backupOpen} onClose={() => setBackupOpen(false)} />
      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  );
}
