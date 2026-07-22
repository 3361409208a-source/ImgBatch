import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { CheckCircle2, Download, Loader2, RefreshCw } from 'lucide-react';
import { api } from '../api/client';
import type { ExtensionInstallStatus, ExtensionItem } from '../api/types';

/** Compact FFmpeg status + one-click install for video/WebM pages. */
export function FfmpegInstallBar() {
  const { t } = useTranslation();
  const [item, setItem] = useState<ExtensionItem | null>(null);
  const [installStatus, setInstallStatus] = useState<ExtensionInstallStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const pollRef = useRef<number | null>(null);

  const stopPoll = () => {
    if (pollRef.current != null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const refresh = useCallback(async () => {
    try {
      const data = await api.listExtensions();
      const ff = data.extensions.find((e) => e.id === 'ffmpeg') ?? null;
      setItem(ff);
      if (data.install) setInstallStatus(data.install);
    } catch {
      setItem(null);
    } finally {
      setLoading(false);
    }
  }, []);

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

  useEffect(() => {
    void refresh();
    return () => stopPoll();
  }, [refresh]);

  const install = async () => {
    setBusy(true);
    setInstallStatus({
      running: true,
      progress: 5,
      message: t('ffmpeg_installing'),
      error: null,
      install_path: null,
    });
    try {
      const res = await api.installExtension('ffmpeg');
      if (res.already_installed) {
        setBusy(false);
        await refresh();
        return;
      }
      if (res.started) {
        stopPoll();
        void checkStatusOnce();
        pollRef.current = window.setInterval(() => {
          void checkStatusOnce();
        }, 600);
      }
    } catch (e) {
      alert(String(e));
      setBusy(false);
      setInstallStatus(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Loader2 size={13} className="animate-spin" />
        {t('ffmpeg_checking')}
      </div>
    );
  }

  const installing = busy || Boolean(installStatus?.running);
  const ready = Boolean(item?.installed);

  if (ready && !installing) {
    return (
      <div className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400">
        <CheckCircle2 size={14} strokeWidth={1.75} />
        <span>{t('ffmpeg_ready')}</span>
        {item?.install_path ? (
          <span className="font-mono opacity-60 truncate max-w-[18rem]" title={item.install_path}>
            {item.install_path}
          </span>
        ) : null}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2 p-3 rounded-md border border-amber-500/30 bg-amber-500/5">
      <p className="text-xs text-muted-foreground">{t('ffmpeg_need_hint')}</p>
      {installing ? (
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2 text-xs">
            <Loader2 size={13} className="animate-spin shrink-0" />
            <span>{installStatus?.message || t('ffmpeg_installing')}</span>
            <span className="font-mono tabular-nums opacity-60">
              {Math.round(installStatus?.progress ?? 0)}%
            </span>
          </div>
          <div className="h-1.5 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${Math.min(100, installStatus?.progress ?? 5)}%` }}
            />
          </div>
        </div>
      ) : (
        <div className="flex flex-wrap items-center gap-2">
          <button type="button" onClick={() => void install()} className="btn-cta h-8 px-3 text-xs">
            <Download size={13} strokeWidth={1.75} />
            {t('ffmpeg_one_click_install')}
          </button>
          <button
            type="button"
            onClick={() => void refresh()}
            className="btn-outline h-8 px-2.5 text-xs"
            title={t('ext_rescan')}
          >
            <RefreshCw size={13} strokeWidth={1.5} />
            {t('ext_rescan')}
          </button>
        </div>
      )}
    </div>
  );
}
