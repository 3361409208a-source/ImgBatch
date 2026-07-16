import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Play, Eye } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { api } from '../api/client';

const MODES = ['prefix', 'suffix', 'replace', 'seq', 'case'];

export function RenamePage() {
  const { t } = useTranslation();
  const { startTask, filteredFiles } = useAppStore();
  const [mode, setMode] = useState('prefix');
  const [prefix, setPrefix] = useState('img_');
  const [suffix, setSuffix] = useState('');
  const [find, setFind] = useState('');
  const [replace, setReplace] = useState('');
  const [seqTemplate, setSeqTemplate] = useState('photo_{num}');
  const [seqStart, setSeqStart] = useState(1);
  const [seqDigits, setSeqDigits] = useState(3);
  const [lowercase, setLowercase] = useState(false);
  const [uppercase, setUppercase] = useState(false);
  const [previewMap, setPreviewMap] = useState<Record<string, string>>({});

  const handlePreview = async () => {
    const res = await api.renamePreview({
      files: filteredFiles,
      mode, prefix, suffix, find, replace: replace,
      seq_template: seqTemplate, seq_start: seqStart, seq_digits: seqDigits,
      lowercase, uppercase,
    });
    setPreviewMap(res.mapping);
  };

  const handleRun = () => {
    startTask('rename', {
      mode, prefix, suffix, find, replace,
      seq_template: seqTemplate, seq_start: seqStart, seq_digits: seqDigits,
      lowercase, uppercase,
    });
  };

  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="flex items-center gap-4">
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted-foreground">{t('mode')}</span>
          <select value={mode} onChange={(e) => setMode(e.target.value)}
            className="px-2 py-1.5 border border-border rounded bg-background cursor-pointer focus:border-primary outline-none">
            {MODES.map((m) => <option key={m} value={m}>{t(m) || m}</option>)}
          </select>
        </label>
        {(mode === 'prefix' || mode === 'suffix') && (
          <>
            <label className="flex flex-col gap-1 text-sm">
              <span className="text-muted-foreground">{t('prefix')}</span>
              <input type="text" value={prefix} onChange={(e) => setPrefix(e.target.value)}
                className="px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none" />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              <span className="text-muted-foreground">{t('suffix')}</span>
              <input type="text" value={suffix} onChange={(e) => setSuffix(e.target.value)}
                className="px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none" />
            </label>
          </>
        )}
        {mode === 'replace' && (
          <>
            <label className="flex flex-col gap-1 text-sm">
              <span className="text-muted-foreground">{t('find')}</span>
              <input type="text" value={find} onChange={(e) => setFind(e.target.value)}
                className="px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none" />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              <span className="text-muted-foreground">{t('replace_to')}</span>
              <input type="text" value={replace} onChange={(e) => setReplace(e.target.value)}
                className="px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none" />
            </label>
          </>
        )}
        {mode === 'seq' && (
          <>
            <label className="flex flex-col gap-1 text-sm">
              <span className="text-muted-foreground">{t('template')}</span>
              <input type="text" value={seqTemplate} onChange={(e) => setSeqTemplate(e.target.value)}
                className="px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none" />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              <span className="text-muted-foreground">{t('start_seq')}</span>
              <input type="number" value={seqStart} onChange={(e) => setSeqStart(Number(e.target.value))}
                className="w-16 px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none" />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              <span className="text-muted-foreground">{t('digits')}</span>
              <input type="number" value={seqDigits} onChange={(e) => setSeqDigits(Number(e.target.value))}
                className="w-16 px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none" />
            </label>
          </>
        )}
        {mode === 'case' && (
          <div className="flex gap-4 pt-6">
            <label className="flex items-center gap-1 text-sm cursor-pointer">
              <input type="checkbox" checked={lowercase} onChange={(e) => setLowercase(e.target.checked)} className="accent-primary cursor-pointer" />
              {t('lowercase')}
            </label>
            <label className="flex items-center gap-1 text-sm cursor-pointer">
              <input type="checkbox" checked={uppercase} onChange={(e) => setUppercase(e.target.checked)} className="accent-primary cursor-pointer" />
              {t('uppercase')}
            </label>
          </div>
        )}
      </div>
      <div className="flex gap-2">
        <button onClick={handlePreview}
          className="btn-outline">
          <Eye size={16} />{t('preview_rename')}
        </button>
        <button onClick={handleRun}
          className="btn-cta">
          <Play size={14} strokeWidth={1.75} />{t('run_rename')}
        </button>
      </div>
      {Object.keys(previewMap).length > 0 && (
        <div className="max-h-48 overflow-auto border border-border rounded-md p-2 text-xs font-mono">
          {Object.entries(previewMap).slice(0, 50).map(([old, newN]) => (
            <div key={old} className="flex gap-2">
              <span className="text-destructive">{old}</span>
              <span className="text-muted-foreground">-&gt;</span>
              <span className="text-primary">{newN}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
