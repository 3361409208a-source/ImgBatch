import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Download, RefreshCw, CheckCircle2, Package, FolderOpen, Loader2 } from 'lucide-react';
import { api } from '../api/client';
import type { ExtensionCatalogResponse, ExtensionInstallStatus, ExtensionItem } from '../api/types';
import { FALLBACK_EXTENSION_CATALOG } from '../utils/extensionCatalog';

interface ExtensionPackPanelProps {
  onUnlocked?: () => void;
  compact?: boolean;
}

function extLabel(item: ExtensionItem, lang: string): string {
  return lang.startsWith('zh') ? item.name : item.name_en;
}

function extDescription(item: ExtensionItem, lang: string): string {
  return lang.startsWith('zh') ? item.description : item.description_en;
}

function extSizeHint(item: ExtensionItem, lang: string): string {
  return lang.startsWith('zh') ? item.size_hint : item.size_hint_en;
}

function extUnlocks(item: ExtensionItem, lang: string): string[] {
  return lang.startsWith('zh') ? item.unlocks : item.unlocks_en;
}

export function ExtensionPackPanel({ onUnlocked, compact = false }: ExtensionPackPanelProps) {
  const { t, i18n } = useTranslation();
  const [catalog, setCatalog] = useState<ExtensionCatalogResponse | null>(null);
  const [installStatus, setInstallStatus] = useState<ExtensionInstallStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [apiOffline, setApiOffline] = useState(false);
  const pollRef = useRef<number | null>(null);

  const stopPoll = () => {
    if (pollRef.current != null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listExtensions();
      setCatalog(data);
      setApiOffline(false);
      if (data.install) setInstallStatus(data.install);
      if (data.locked_count === 0) onUnlocked?.();
    } catch {
      setCatalog(FALLBACK_EXTENSION_CATALOG);
      setApiOffline(true);
    } finally {
      setLoading(false);
    }
  }, [onUnlocked]);

  const checkStatusOnce = useCallback(async () => {
    try {
      const st = await api.extensionInstallStatus();
      setInstallStatus(st);
      if (!st.running) {
        stopPoll();
        setBusy(false);
        await refresh();
        if (st.error) alert(st.error);
      }
    } catch {
      /* ignore */
    }
  }, [refresh]);

  const pollInstall = useCallback(() => {
    stopPoll();
    void checkStatusOnce();
    pollRef.current = window.setInterval(() => {
      void checkStatusOnce();
    }, 600);
  }, [checkStatusOnce]);

  useEffect(() => {
    void refresh();
    return () => stopPoll();
  }, [refresh]);

  const oneClickInstall = async (extId: string) => {
    setBusy(true);
    setInstallStatus({
      running: true,
      progress: 5,
      message: t('ext_installing'),
      error: null,
      install_path: null,
    });
    try {
      const res = await api.installExtension(extId);
      if (res.already_installed) {
        setBusy(false);
        await refresh();
        return;
      }
      if (res.started) pollInstall();
    } catch (e) {
      alert(String(e));
      setBusy(false);
      setInstallStatus(null);
    }
  };

  const pickExtensionPath = async (extId: string) => {
    setBusy(true);
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const path = await invoke<string | null>('pick_executable');
      if (!path) return;
      await api.setExtensionPath(extId, path);
      await refresh();
    } catch (e) {
      alert(String(e));
    } finally {
      setBusy(false);
    }
  };

  if (loading && !catalog) {
    return (
      <div className="rounded-lg border-2 border-primary/30 bg-primary/5 px-4 py-3 text-xs text-muted-foreground">
        {t('ext_loading')}
      </div>
    );
  }

  const catalogData = catalog ?? FALLBACK_EXTENSION_CATALOG;
  const allInstalled = catalogData.locked_count === 0;
  const installing = Boolean(installStatus?.running || busy);

  if (allInstalled && compact) {
    return (
      <div className="flex items-center gap-2 text-xs text-primary">
        <CheckCircle2 size={14} />
        {t('ext_all_unlocked')}
      </div>
    );
  }

  return (
    <div className="rounded-lg border-2 border-primary/40 bg-primary/5 px-4 py-3 space-y-3 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2">
          <Package size={18} className="text-primary mt-0.5 shrink-0" />
          <div>
            <h3 className="text-sm font-semibold text-foreground">
              {allInstalled ? t('ext_all_unlocked') : t('ext_unlock_title')}
            </h3>
            {!allInstalled && (
              <p className="text-xs text-muted-foreground mt-0.5">{t('ext_unlock_subtitle')}</p>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={() => void refresh()}
          disabled={installing}
          className="btn-ghost h-7 text-xs shrink-0"
          title={t('ext_rescan')}
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          {t('ext_rescan')}
        </button>
      </div>

      {apiOffline && (
        <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1.5">
          {t('ext_api_offline')}
        </p>
      )}

      {installing && installStatus && (
        <div className="rounded-md border border-primary/20 bg-background/80 px-3 py-2 space-y-1.5">
          <div className="flex items-center gap-2 text-xs text-primary">
            <Loader2 size={14} className="animate-spin" />
            {installStatus.message || t('ext_installing')}
          </div>
          <div className="h-1.5 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${Math.max(5, installStatus.progress)}%` }}
            />
          </div>
        </div>
      )}

      <div className="space-y-2">
        {catalogData.extensions.map((item) => (
          <div
            key={item.id}
            className={`rounded-md border px-3 py-2.5 ${
              item.installed
                ? 'border-primary/30 bg-background/80'
                : 'border-border bg-background/60'
            }`}
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                {item.installed ? (
                  <CheckCircle2 size={15} className="text-primary shrink-0" />
                ) : (
                  <Package size={15} className="text-muted-foreground shrink-0" />
                )}
                <span className="text-sm font-medium truncate">{extLabel(item, i18n.language)}</span>
                <span className="text-[10px] text-muted-foreground">{extSizeHint(item, i18n.language)}</span>
              </div>
              {!item.installed && (
                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => void oneClickInstall(item.id)}
                    disabled={installing}
                    className="btn-cta h-7 text-xs px-2.5"
                  >
                    <Download size={13} />
                    {t('ext_one_click_install')}
                  </button>
                  <button
                    type="button"
                    onClick={() => void pickExtensionPath(item.id)}
                    disabled={installing}
                    className="btn-ghost h-7 text-xs px-2"
                    title={t('ext_manual_path')}
                  >
                    <FolderOpen size={13} />
                  </button>
                </div>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-1.5">{extDescription(item, i18n.language)}</p>
            {item.install_dir && !item.installed && (
              <p className="text-[10px] text-muted-foreground mt-1 font-mono truncate" title={item.install_dir}>
                {t('ext_install_to')}: {item.install_dir}
              </p>
            )}
            {item.installed && item.install_path && (
              <p className="text-[10px] font-mono text-muted-foreground mt-1 truncate" title={item.install_path}>
                {item.install_path}
              </p>
            )}
            <ul className="mt-2 flex flex-wrap gap-1.5">
              {extUnlocks(item, i18n.language).map((feat) => (
                <li
                  key={feat}
                  className={`text-[10px] px-1.5 py-0.5 rounded border ${
                    item.installed
                      ? 'border-primary/20 bg-primary/10 text-primary'
                      : 'border-border bg-muted/40 text-muted-foreground'
                  }`}
                >
                  {feat}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {!allInstalled && (
        <p className="text-[11px] text-muted-foreground">{t('ext_install_hint')}</p>
      )}
    </div>
  );
}
