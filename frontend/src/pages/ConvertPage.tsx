import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Play } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { OutputOptions } from '../components/OutputOptions';
import { ToolPanel } from '../components/ToolPanel';
import { api } from '../api/client';
import type { ConvertCatalog } from '../utils/convertFormats';
import {
  FALLBACK_CONVERT_CATALOG,
  groupTargets,
  targetSupportsQuality,
} from '../utils/convertFormats';

function requireOut(replace: boolean, out: string): boolean {
  if (!replace && !out.trim()) {
    alert('Please set an output folder when not replacing originals');
    return false;
  }
  return true;
}

export function ConvertPage() {
  const { t } = useTranslation();
  const { startTask } = useAppStore();
  const [catalog, setCatalog] = useState<ConvertCatalog>(FALLBACK_CONVERT_CATALOG);
  const [targetFmt, setTargetFmt] = useState('.png');
  const [quality, setQuality] = useState(85);
  const [replace, setReplace] = useState(true);
  const [doBackup, setDoBackup] = useState(true);
  const [out, setOut] = useState('');

  useEffect(() => {
    void api.convertFormats().then(setCatalog).catch(() => {
      setCatalog(FALLBACK_CONVERT_CATALOG);
    });
  }, []);

  const { common, other } = groupTargets(catalog);
  const showQuality = targetSupportsQuality(catalog, targetFmt);

  const applyPreset = (preset: ConvertCatalog['presets'][number]) => {
    setTargetFmt(preset.target_fmt);
    if (preset.quality != null) setQuality(preset.quality);
  };

  return (
    <ToolPanel>
      <div className="flex flex-col gap-2">
        <span className="text-sm text-muted-foreground">{t('convert_common_presets')}</span>
        <div className="flex flex-wrap gap-2">
          {catalog.presets.map((preset) => (
            <button
              key={preset.id}
              type="button"
              title={preset.hint}
              onClick={() => applyPreset(preset)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md border transition-colors cursor-pointer
                ${targetFmt === preset.target_fmt
                  ? 'border-primary bg-primary/10 text-primary'
                  : 'border-border bg-background hover:bg-muted text-foreground'
                }`}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-1 text-sm w-48">
          <span className="text-muted-foreground">{t('to_format')}</span>
          <select
            value={targetFmt}
            onChange={(e) => setTargetFmt(e.target.value)}
            className="px-2 py-1.5 border border-border rounded bg-background cursor-pointer focus:border-primary outline-none"
          >
            {common.length > 0 && (
              <optgroup label={t('convert_group_common')}>
                {common.map((f) => (
                  <option key={f.ext} value={f.ext}>{f.ext}</option>
                ))}
              </optgroup>
            )}
            {other.length > 0 && (
              <optgroup label={t('convert_group_other')}>
                {other.map((f) => (
                  <option key={f.ext} value={f.ext}>{f.ext}</option>
                ))}
              </optgroup>
            )}
          </select>
        </label>

        {showQuality && (
          <label className="flex flex-col gap-1 text-sm w-56">
            <span className="text-muted-foreground">{t('quality')} {quality}</span>
            <input
              type="range"
              min={1}
              max={100}
              value={quality}
              onChange={(e) => setQuality(Number(e.target.value))}
              className="cursor-pointer"
            />
          </label>
        )}
      </div>

      {(catalog.features.heic_input || catalog.features.avif_output) && (
        <p className="text-xs text-muted-foreground">
          {catalog.features.heic_input && t('convert_heic_hint')}
          {catalog.features.heic_input && catalog.features.avif_output && ' · '}
          {catalog.features.avif_output && t('convert_avif_hint')}
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

      <button
        onClick={() => {
          if (!requireOut(replace, out)) return;
          void startTask('convert', {
            target_fmt: targetFmt,
            quality: showQuality ? quality : undefined,
            do_backup: doBackup,
            replace,
            out: replace ? null : out,
          });
        }}
        className="btn-cta w-fit"
      >
        <Play size={16} />
        {t('start_convert')}
      </button>
    </ToolPanel>
  );
}
