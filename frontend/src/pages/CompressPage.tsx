import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Play } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { OutputOptions } from '../components/OutputOptions';
import { ToolPanel } from '../components/ToolPanel';
import { api } from '../api/client';

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
  const [quality, setQuality] = useState(75);
  const [resizePct, setResizePct] = useState(100);
  const [exifMode, setExifMode] = useState('keep');
  const [replace, setReplace] = useState(true);
  const [doBackup, setDoBackup] = useState(true);
  const [out, setOut] = useState('');
  const [estimate, setEstimate] = useState<{ before: number; after: number } | null>(null);

  useEffect(() => {
    if (filteredFiles.length === 0) {
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
  }, [filteredFiles, quality, resizePct]);

  const handleStart = () => {
    if (!requireOut(replace, out)) return;
    void startTask('compress', {
      quality,
      resize_pct: resizePct,
      do_backup: doBackup,
      replace,
      out: replace ? null : out,
      exif_mode: exifMode,
    });
  };

  return (
    <ToolPanel>
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
      {estimate && (
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
        {t('start_compress')}
      </button>
    </ToolPanel>
  );
}
