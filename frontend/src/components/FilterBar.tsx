import { useTranslation } from 'react-i18next';
import { Search, RotateCcw } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { DOC_FILTER_FORMATS } from '../utils/docFormats';

const IMAGE_FORMATS = ['ALL', 'PNG', 'JPEG', 'WEBP', 'BMP', 'TIFF', 'GIF', 'ICO', 'AVIF', 'HEIC', 'WEBM'];
const SIZES = ['all', 'lt_50kb', 'lt_100kb', 'lt_500kb', 'lt_1mb', '100kb_1mb', 'gt_500kb', 'gt_1mb'];

export function FilterBar() {
  const { t } = useTranslation();
  const s = useAppStore();
  const formats = s.scanKind === 'document' ? DOC_FILTER_FORMATS : IMAGE_FORMATS;

  return (
    <div className="flex flex-wrap items-center gap-2 px-4 py-2 bg-[color:var(--color-surface-2)] border-b border-border">
      <div className="relative shrink-0">
        <Search size={13} strokeWidth={1.5} className="absolute left-2 top-1/2 -translate-y-1/2 text-[color:var(--color-muted-fg)] pointer-events-none" />
        <input
          type="text"
          placeholder={t('filter_name')}
          value={s.filterName}
          onChange={(e) => s.setFilter('filterName', e.target.value)}
          className="field-sm w-36 pl-7"
        />
      </div>

      <select
        value={s.filterFormat}
        onChange={(e) => s.setFilter('filterFormat', e.target.value)}
        className="field-sm cursor-pointer shrink-0"
      >
        {formats.map((f) => (
          <option key={f} value={f}>
            {f === 'ALL' ? t('filter_size_all') : f}
          </option>
        ))}
      </select>

      <select
        value={s.filterSizePreset}
        onChange={(e) => s.setFilter('filterSizePreset', e.target.value)}
        className="field-sm cursor-pointer min-w-[7rem] shrink-0"
      >
        {SIZES.map((sz) => (
          <option key={sz} value={sz}>
            {t(`filter_size_${sz}`)}
          </option>
        ))}
      </select>

      <div className="flex items-center gap-1.5 shrink-0">
        <span className="label-muted whitespace-nowrap">{t('filter_dim')}</span>
        <input
          type="text"
          placeholder="W"
          value={s.filterMinWidth}
          onChange={(e) => s.setFilter('filterMinWidth', e.target.value)}
          className="field-sm w-12 text-center font-mono"
        />
        <span className="text-[11px] text-[color:var(--color-muted-fg)]">×</span>
        <input
          type="text"
          placeholder="H"
          value={s.filterMinHeight}
          onChange={(e) => s.setFilter('filterMinHeight', e.target.value)}
          className="field-sm w-12 text-center font-mono"
        />
      </div>

      <button type="button" onClick={() => void s.applyFilter()} className="btn-primary h-7 text-xs shrink-0">
        {t('filter')}
      </button>
      <button
        type="button"
        onClick={() => {
          s.setFilter('filterName', '');
          s.setFilter('filterFormat', 'ALL');
          s.setFilter('filterSizePreset', 'all');
          s.setFilter('filterMinWidth', '');
          s.setFilter('filterMinHeight', '');
          void s.applyFilter();
        }}
        className="btn-ghost h-7 px-2 shrink-0"
        title="Reset"
      >
        <RotateCcw size={13} strokeWidth={1.5} />
      </button>

      <div className="ml-auto text-[11px] font-mono text-[color:var(--color-muted-fg)] tabular-nums">
        {s.filteredFiles.length}
        <span className="opacity-40"> / </span>
        {s.allFiles.length}
      </div>
    </div>
  );
}
