import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Archive, X, RotateCcw, Trash2 } from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/appStore';

interface BackupManagerProps {
  open: boolean;
  onClose: () => void;
}

export function BackupManager({ open, onClose }: BackupManagerProps) {
  const { t } = useTranslation();
  const { folder, refreshFiles, setStatusMessage } = useAppStore();
  const [backups, setBackups] = useState<string[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    if (!folder) {
      setBackups([]);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await api.listBackups(folder);
      setBackups(res.backups || []);
      setSelected([]);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) void load();
  }, [open, folder]);

  if (!open) return null;

  const toggle = (path: string) => {
    setSelected((prev) =>
      prev.includes(path) ? prev.filter((p) => p !== path) : [...prev, path],
    );
  };

  const handleRestore = async () => {
    if (selected.length !== 1) {
      alert('Select exactly one backup to restore');
      return;
    }
    try {
      const res = await api.restoreBackup(selected[0], folder);
      setStatusMessage(`Restored ${res.restored} files`);
      await refreshFiles();
      onClose();
    } catch (e) {
      setError(String(e));
    }
  };

  const handleClear = async () => {
    const targets = selected.length > 0 ? selected : backups;
    if (targets.length === 0) return;
    if (!confirm(`Delete ${targets.length} backup(s)?`)) return;
    try {
      const res = await api.clearBackups(targets);
      setStatusMessage(`Deleted ${res.deleted} backups`);
      await load();
    } catch (e) {
      setError(String(e));
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-[2px]">
      <div className="w-full max-w-lg bg-surface border border-border rounded-lg shadow-xl p-4 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold tracking-tight flex items-center gap-2">
            <Archive size={15} strokeWidth={1.5} className="text-primary" />
            {t('backup_mgr')}
          </h2>
          <button type="button" onClick={onClose} className="btn-ghost h-7 w-7 p-0">
            <X size={15} strokeWidth={1.5} />
          </button>
        </div>
        {!folder && <p className="text-[13px] text-[color:var(--color-muted-fg)]">{t('select_folder_first')}</p>}
        {loading && <p className="text-xs text-[color:var(--color-muted-fg)]">Loading...</p>}
        {error && <p className="text-xs text-destructive">{error}</p>}
        <div className="max-h-64 overflow-auto border border-border rounded-md bg-[color:var(--color-surface-2)]">
          {backups.length === 0 && !loading ? (
            <p className="px-3 py-8 text-center text-[13px] text-[color:var(--color-muted-fg)]">No backups found</p>
          ) : (
            <ul className="divide-y divide-border text-[11px] font-mono">
              {backups.map((b) => (
                <li key={b}>
                  <label className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-muted">
                    <input type="checkbox" checked={selected.includes(b)} onChange={() => toggle(b)} />
                    <span className="truncate" title={b}>
                      {b}
                    </span>
                  </label>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="flex gap-2 justify-end pt-1">
          <button
            type="button"
            onClick={() => void handleRestore()}
            disabled={selected.length !== 1}
            className="btn-outline disabled:opacity-40"
          >
            <RotateCcw size={13} strokeWidth={1.5} />
            Restore
          </button>
          <button
            type="button"
            onClick={() => void handleClear()}
            disabled={backups.length === 0}
            className="btn-danger disabled:opacity-40"
          >
            <Trash2 size={13} strokeWidth={1.5} />
            Clear
          </button>
        </div>
      </div>
    </div>
  );
}
