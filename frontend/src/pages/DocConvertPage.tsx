import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Play } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { OutputOptions } from '../components/OutputOptions';
import { ExtensionPackPanel } from '../components/ExtensionPackPanel';
import { api } from '../api/client';
import type { DocCatalog } from '../utils/docFormats';
import {
  FALLBACK_DOC_CATALOG,
  groupDocTargets,
  isPdfTarget,
  isRasterDocTarget,
} from '../utils/docFormats';

function requireOut(replace: boolean, out: string): boolean {
  if (!replace && !out.trim()) {
    alert('Please set an output folder when not replacing originals');
    return false;
  }
  return true;
}

export function DocConvertPage() {
  const { t } = useTranslation();
  const { startTask } = useAppStore();
  const [catalog, setCatalog] = useState<DocCatalog>(FALLBACK_DOC_CATALOG);
  const [targetFmt, setTargetFmt] = useState('.pdf');
  const [dpi, setDpi] = useState(150);
  const [pageMode, setPageMode] = useState<'all' | 'first'>('all');
  const [quality, setQuality] = useState(85);
  const [replace, setReplace] = useState(true);
  const [doBackup, setDoBackup] = useState(true);
  const [out, setOut] = useState('');

  const reloadCatalog = useCallback(() => {
    void api.docFormats().then(setCatalog).catch(() => setCatalog(FALLBACK_DOC_CATALOG));
  }, []);

  useEffect(() => {
    reloadCatalog();
  }, [reloadCatalog]);

  const { common, other } = groupDocTargets(catalog);
  const showPdfOptions = isRasterDocTarget(targetFmt);
  const showQuality = targetFmt.toLowerCase() === '.jpg' || targetFmt.toLowerCase() === '.jpeg';

  const applyPreset = (preset: DocCatalog['presets'][number]) => {
    setTargetFmt(preset.target_fmt);
  };

  return (
    <div className="flex flex-col gap-4 p-4">
      <ExtensionPackPanel onUnlocked={reloadCatalog} />

      <p className="text-xs text-muted-foreground max-w-2xl">{t('doc_convert_hint')}</p>

      <div className="flex flex-col gap-2">
        <span className="text-sm text-muted-foreground">{t('doc_common_presets')}</span>
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
          <span className="text-muted-foreground">{t('doc_target_format')}</span>
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

        {showPdfOptions && (
          <>
            <label className="flex flex-col gap-1 text-sm w-40">
              <span className="text-muted-foreground">{t('doc_pdf_pages')}</span>
              <select
                value={pageMode}
                onChange={(e) => setPageMode(e.target.value as 'all' | 'first')}
                className="px-2 py-1.5 border border-border rounded bg-background cursor-pointer"
              >
                <option value="all">{t('doc_pdf_pages_all')}</option>
                <option value="first">{t('doc_pdf_pages_first')}</option>
              </select>
            </label>
            <label className="flex flex-col gap-1 text-sm w-48">
              <span className="text-muted-foreground">{t('doc_pdf_dpi')} {dpi}</span>
              <input
                type="range"
                min={72}
                max={300}
                value={dpi}
                onChange={(e) => setDpi(Number(e.target.value))}
                className="cursor-pointer"
              />
            </label>
          </>
        )}

        {showQuality && (
          <label className="flex flex-col gap-1 text-sm w-48">
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

      {!catalog.features.pymupdf && (
        <p className="text-xs text-muted-foreground">{t('doc_pymupdf_missing')}</p>
      )}
      {isPdfTarget(targetFmt) && catalog.features.libreoffice && (
        <p className="text-xs text-muted-foreground">{t('doc_office_to_pdf_hint')}</p>
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
          void startTask('doc_convert', {
            target_fmt: targetFmt,
            dpi,
            page_mode: pageMode,
            quality: showQuality ? quality : undefined,
            do_backup: doBackup,
            replace,
            out: replace ? null : out,
          });
        }}
        className="btn-cta w-fit"
      >
        <Play size={16} />
        {t('start_doc_convert')}
      </button>
    </div>
  );
}
