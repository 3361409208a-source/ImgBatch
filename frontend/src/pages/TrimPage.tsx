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

export function TrimPage() {
  const { t } = useTranslation();
  const { startTask } = useAppStore();
  const [padding, setPadding] = useState(4);
  const [replace, setReplace] = useState(true);
  const [doBackup, setDoBackup] = useState(true);
  const [out, setOut] = useState('');

  return (
    <ToolPanel>
      <label className="flex flex-col gap-1 text-sm w-48">
        <span className="text-muted-foreground">{t('padding')}</span>
        <input type="number" value={padding} onChange={(e) => setPadding(Number(e.target.value))} min="0"
          className="px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none" />
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
        void startTask('trim', { padding, do_backup: doBackup, replace, out: replace ? null : out });
      }}
        className="btn-cta w-fit">
        <Play size={16} />{t('start_trim')}
      </button>
    </ToolPanel>
  );
}
