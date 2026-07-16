import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Play } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { OutputOptions } from '../components/OutputOptions';

const FORMATS = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.gif', '.ico'];

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
  const [targetFmt, setTargetFmt] = useState('.png');
  const [replace, setReplace] = useState(true);
  const [doBackup, setDoBackup] = useState(true);
  const [out, setOut] = useState('');

  return (
    <div className="flex flex-col gap-4 p-4">
      <label className="flex flex-col gap-1 text-sm w-48">
        <span className="text-muted-foreground">{t('to_format')}</span>
        <select value={targetFmt} onChange={(e) => setTargetFmt(e.target.value)}
          className="px-2 py-1.5 border border-border rounded bg-background cursor-pointer focus:border-primary outline-none">
          {FORMATS.map((f) => <option key={f} value={f}>{f}</option>)}
        </select>
      </label>
      <OutputOptions replace={replace} doBackup={doBackup} out={out}
        onChange={(k, v) => {
          if (k === 'replace') setReplace(v as boolean);
          if (k === 'do_backup') setDoBackup(v as boolean);
          if (k === 'out') setOut(v as string);
        }}
      />
      <button onClick={() => {
        if (!requireOut(replace, out)) return;
        void startTask('convert', { target_fmt: targetFmt, do_backup: doBackup, replace, out: replace ? null : out });
      }}
        className="btn-cta w-fit">
        <Play size={16} />{t('start_convert')}
      </button>
    </div>
  );
}
