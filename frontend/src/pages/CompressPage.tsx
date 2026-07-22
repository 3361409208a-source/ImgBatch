import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Play } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { OutputOptions } from '../components/OutputOptions';
import { ToolPanel } from '../components/ToolPanel';
import { FfmpegInstallBar } from '../components/FfmpegInstallBar';
import { api } from '../api/client';

type CompressMode = 'normal' | 'balanced' | 'webm';

function requireOut(replace: boolean, out: string): boolean {
  if (!replace && !out.trim()) {
    alert('Please set an output folder when not replacing originals');
    return false;
  }
  return true;
}

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(2)} MB`;
}

export function CompressPage() {
  const { t } = useTranslation();
  const { startTask, filteredFiles } = useAppStore();
  const [mode, setMode] = useState<CompressMode>('normal');
  const [quality, setQuality] = useState(75);
  const [resizePct, setResizePct] = useState(100);
  const [exifMode, setExifMode] = useState('keep');
  const [targetMb, setTargetMb] = useState(1.15);
  const [maxEdge, setMaxEdge] = useState(256);
  const [crf, setCrf] = useState(40);
  const [fps, setFps] = useState(24);
  const [keepAlpha, setKeepAlpha] = useState(true);
  const [replace, setReplace] = useState(true);
  const [doBackup, setDoBackup] = useState(true);
  const [out, setOut] = useState('');
  const [estimate, setEstimate] = useState<{ before: number; after: number } | null>(null);

  useEffect(() => {
    if (mode !== 'normal' || filteredFiles.length === 0) {
      setEstimate(null);
      return;
    }
    let cancelled = false;
    const timer = setTimeout(() => {
      void api
        .compressEstimate(filteredFiles, quality, resizePct)
        .then((res) => {
          if (!cancelled) {
            setEstimate({ before: res.total_before, after: res.total_after });
          }
        })
        .catch(() => {
          if (!cancelled) setEstimate(null);
        });
    }, 300);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [filteredFiles, quality, resizePct, mode]);

  const handleStart = () => {
    if (!requireOut(replace, out)) return;
    if (mode === 'balanced') {
      void startTask('compress', {
        mode: 'balanced',
        target_mb: targetMb,
        do_backup: doBackup,
        replace,
        out: replace ? null : out,
      });
      return;
    }
    if (mode === 'webm') {
      void startTask('compress', {
        mode: 'webm',
        max_edge: maxEdge,
        crf,
        fps,
        keep_alpha: keepAlpha,
        do_backup: doBackup,
        replace,
        out: replace ? null : out,
      });
      return;
    }
    void startTask('compress', {
      quality,
      resize_pct: resizePct,
      do_backup: doBackup,
      replace,
      out: replace ? null : out,
      exif_mode: exifMode,
    });
  };

  const modeBtn = (key: CompressMode, label: string) => (
    <button
      type="button"
      key={key}
      onClick={() => setMode(key)}
      className={`px-3 py-1.5 text-sm rounded-md border transition-colors ${
        mode === key
          ? 'border-primary bg-primary/10 text-foreground'
          : 'border-border text-muted-foreground hover:border-primary/40'
      }`}
    >
      {label}
    </button>
  );

  return (
    <ToolPanel>
      <div className="flex flex-wrap gap-2">
        {modeBtn('normal', t('compress_mode_normal'))}
        {modeBtn('balanced', t('compress_mode_balanced'))}
        {modeBtn('webm', t('compress_mode_webm'))}
      </div>

      {mode === 'balanced' ? (
        <div className="flex flex-col gap-2">
          <label className="flex flex-col gap-1.5 w-48">
            <span className="label-muted">{t('target_mb')}</span>
            <input
              type="number"
              min={0.1}
              step={0.05}
              value={targetMb}
              onChange={(e) => setTargetMb(Number(e.target.value))}
              className="field"
            />
          </label>
          <p className="text-xs text-muted-foreground max-w-xl">{t('compress_balanced_hint')}</p>
        </div>
      ) : mode === 'webm' ? (
        <div className="flex flex-col gap-3">
          <FfmpegInstallBar />
          <div className="flex flex-wrap items-end gap-6">
            <label className="flex flex-col gap-1.5 w-28">
              <span className="label-muted">{t('webm_max_edge')}</span>
              <input
                type="number"
                min={32}
                max={4096}
                value={maxEdge}
                onChange={(e) => setMaxEdge(Number(e.target.value))}
                className="field"
              />
            </label>
            <label className="flex flex-col gap-1.5 w-24">
              <span className="label-muted">{t('webm_crf')}</span>
              <input
                type="number"
                min={0}
                max={63}
                value={crf}
                onChange={(e) => setCrf(Number(e.target.value))}
                className="field"
              />
            </label>
            <label className="flex flex-col gap-1.5 w-24">
              <span className="label-muted">{t('webm_fps')}</span>
              <input
                type="number"
                min={1}
                max={60}
                value={fps}
                onChange={(e) => setFps(Number(e.target.value))}
                className="field"
              />
            </label>
          </div>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={keepAlpha}
              onChange={(e) => setKeepAlpha(e.target.checked)}
              className="accent-primary"
            />
            {t('webm_keep_alpha')}
          </label>
          <p className="text-xs text-muted-foreground max-w-xl">{t('compress_webm_hint')}</p>
        </div>
      ) : (
        <div className="flex items-end gap-8 flex-wrap">
          <label className="flex flex-col gap-1.5">
            <span className="label-muted">{t('quality')}</span>
            <div className="flex items-center gap-2.5">
              <input type="range" min="1" max="100" value={quality} onChange={(e) => setQuality(Number(e.target.value))} />
              <span className="font-mono text-xs w-7 tabular-nums text-foreground">{quality}</span>
            </div>
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="label-muted">{t('resize')} %</span>
            <div className="flex items-center gap-2.5">
              <input type="range" min="1" max="100" value={resizePct} onChange={(e) => setResizePct(Number(e.target.value))} />
              <span className="font-mono text-xs w-8 tabular-nums text-foreground">{resizePct}%</span>
            </div>
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="label-muted">EXIF</span>
            <select value={exifMode} onChange={(e) => setExifMode(e.target.value)} className="field cursor-pointer w-36">
              <option value="keep">{t('exif_keep')}</option>
              <option value="strip">{t('exif_strip')}</option>
              <option value="orientation_only">{t('exif_orient')}</option>
            </select>
          </label>
        </div>
      )}

      {estimate && mode === 'normal' && (
        <p className="text-[12px] font-mono text-[color:var(--color-muted-fg)] tabular-nums">
          {formatBytes(estimate.before)}
          <span className="opacity-40 mx-1.5">-&gt;</span>
          {formatBytes(estimate.after)}
          {estimate.before > 0 ? (
            <span className="ml-2 text-primary">-{Math.round((1 - estimate.after / estimate.before) * 100)}%</span>
          ) : null}
        </p>
      )}
      <OutputOptions
        replace={replace}
        doBackup={doBackup}
        out={out}
        onChange={(k, v) => {
          if (k === 'replace') setReplace(v as boolean);
          if (k === 'do_backup') setDoBackup(v as boolean);
          if (k === 'out') setOut(v as string);
        }}
      />
      <button type="button" onClick={handleStart} className="btn-cta w-fit">
        <Play size={14} strokeWidth={1.75} />
        {mode === 'balanced'
          ? t('start_balanced_compress')
          : mode === 'webm'
            ? t('start_webm_compress')
            : t('start_compress')}
      </button>
    </ToolPanel>
  );
}
