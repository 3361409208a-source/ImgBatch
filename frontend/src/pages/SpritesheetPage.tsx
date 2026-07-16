import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Play } from 'lucide-react';
import { useAppStore } from '../store/appStore';

const LAYOUTS = ['auto', 'grid', 'horizontal', 'vertical'];

export function SpritesheetPage() {
  const { t } = useTranslation();
  const { startTask, folder, filteredFiles } = useAppStore();
  const [layout, setLayout] = useState('auto');
  const [spacing, setSpacing] = useState(2);
  const [trim, setTrim] = useState(true);
  const [trimPadding, setTrimPadding] = useState(2);
  const [alphaThreshold, setAlphaThreshold] = useState(28);
  const [columns, setColumns] = useState(0);
  const [maxWidth, setMaxWidth] = useState(0);
  const [powerOfTwo, setPowerOfTwo] = useState(false);
  const [exportJson, setExportJson] = useState(true);
  const [output, setOutput] = useState('');

  const handleBuild = () => {
    const outputPath = output || `${folder}\\spritesheet.png`;
    startTask('spritesheet', {
      output: outputPath,
      layout, spacing, trim, trim_padding: trimPadding,
      alpha_threshold: alphaThreshold, columns, max_width: maxWidth,
      power_of_two: powerOfTwo, export_json: exportJson,
    });
  };

  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="flex items-center gap-6 flex-wrap">
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted-foreground">{t('layout')}</span>
          <select value={layout} onChange={(e) => setLayout(e.target.value)}
            className="px-2 py-1.5 border border-border rounded bg-background cursor-pointer focus:border-primary outline-none">
            {LAYOUTS.map((l) => <option key={l} value={l}>{t(`layout_${l}`)}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted-foreground">{t('spacing')}</span>
          <input type="number" value={spacing} onChange={(e) => setSpacing(Number(e.target.value))} min="0"
            className="w-16 px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none" />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted-foreground">{t('columns')} (0=auto)</span>
          <input type="number" value={columns} onChange={(e) => setColumns(Number(e.target.value))} min="0"
            className="w-16 px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none" />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted-foreground">{t('max_width')} (0=smart)</span>
          <input type="number" value={maxWidth} onChange={(e) => setMaxWidth(Number(e.target.value))} min="0"
            className="w-20 px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none" />
        </label>
      </div>
      <div className="flex items-center gap-6 flex-wrap">
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" checked={trim} onChange={(e) => setTrim(e.target.checked)} className="accent-primary cursor-pointer" />
          {t('trim')}
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted-foreground">Trim Padding</span>
          <input type="number" value={trimPadding} onChange={(e) => setTrimPadding(Number(e.target.value))} min="0"
            className="w-16 px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none" />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted-foreground">{t('alpha_threshold')}</span>
          <input type="number" value={alphaThreshold} onChange={(e) => setAlphaThreshold(Number(e.target.value))} min="0" max="255"
            className="w-16 px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none" />
        </label>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" checked={powerOfTwo} onChange={(e) => setPowerOfTwo(e.target.checked)} className="accent-primary cursor-pointer" />
          {t('power_of_two')}
        </label>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" checked={exportJson} onChange={(e) => setExportJson(e.target.checked)} className="accent-primary cursor-pointer" />
          {t('export_json')}
        </label>
      </div>
      <label className="flex flex-col gap-1 text-sm">
        <span className="text-muted-foreground">{t('output_file')}</span>
        <input type="text" value={output} onChange={(e) => setOutput(e.target.value)} placeholder={`${folder}\\spritesheet.png`}
          className="px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none" />
      </label>
      <p className="text-xs text-muted-foreground">{filteredFiles.length} files selected</p>
      <button onClick={handleBuild}
        className="btn-cta w-fit">
        <Play size={16} />{t('start_spritesheet')}
      </button>
    </div>
  );
}
