import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Play } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { OutputOptions } from '../components/OutputOptions';
import { ToolPanel } from '../components/ToolPanel';

function requireOut(replace: boolean, out: string): boolean {
  if (!replace && !out.trim()) {
    alert('Please set an output folder when not replacing originals');
    return false;
  }
  return true;
}

export function NormalizePage() {
  const { t } = useTranslation();
  const { startTask } = useAppStore();
  const [alphaThreshold, setAlphaThreshold] = useState(28);
  const [targetHeight, setTargetHeight] = useState(280);
  const [padding, setPadding] = useState(6);
  const [replace, setReplace] = useState(true);
  const [doBackup, setDoBackup] = useState(true);
  const [out, setOut] = useState('');

  return (
    <ToolPanel>
      <div className="flex items-center gap-6 flex-wrap">
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted-foreground">{t('alpha_threshold')}</span>
          <input type="number" value={alphaThreshold} onChange={(e) => setAlphaThreshold(Number(e.target.value))} min="0" max="255"
            className="w-20 px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none" />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted-foreground">{t('target_height')}</span>
          <input type="number" value={targetHeight} onChange={(e) => setTargetHeight(Number(e.target.value))} min="1"
            className="w-24 px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none" />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted-foreground">{t('padding')}</span>
          <input type="number" value={padding} onChange={(e) => setPadding(Number(e.target.value))} min="0"
            className="w-20 px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none" />
        </label>
      </div>
      <OutputOptions replace={replace} doBackup={doBackup} out={out}
        onChange={(k, v) => {
          if (k === 'replace') setReplace(v as boolean);
          if (k === 'do_backup') setDoBackup(v as boolean);
          if (k === 'out') setOut(v as string);
        }}
      />
      <button onClick={() => {
        if (!requireOut(replace, out)) return;
        void startTask('normalize', {
          alpha_threshold: alphaThreshold, target_height: targetHeight, padding,
          do_backup: doBackup, replace, out: replace ? null : out,
        });
      }}
        className="btn-cta w-fit">
        <Play size={16} />{t('start_normalize')}
      </button>
    </ToolPanel>
  );
}
