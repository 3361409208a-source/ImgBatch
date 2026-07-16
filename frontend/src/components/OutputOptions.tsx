import { useTranslation } from 'react-i18next';
import { FolderOpen } from 'lucide-react';

interface OutputOptionsProps {
  replace: boolean;
  doBackup: boolean;
  out: string;
  onChange: (key: string, value: unknown) => void;
  showBackup?: boolean;
}

export function OutputOptions({ replace, doBackup, out, onChange, showBackup = true }: OutputOptionsProps) {
  const { t } = useTranslation();

  const pickOut = async () => {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const path = await invoke<string | null>('pick_folder');
      if (path) {
        onChange('replace', false);
        onChange('out', path);
      }
    } catch {
      const path = window.prompt('Output folder path:');
      if (path) {
        onChange('replace', false);
        onChange('out', path);
      }
    }
  };

  return (
    <div className="flex flex-col gap-2 p-3 rounded-md border border-border bg-[color:var(--color-surface-2)]">
      <label className="flex items-center gap-2 text-[13px] cursor-pointer">
        <input type="radio" checked={replace} onChange={() => onChange('replace', true)} />
        {t('replace_orig')}
      </label>
      <label className="flex items-center gap-2 text-[13px] cursor-pointer flex-wrap">
        <input type="radio" checked={!replace} onChange={() => onChange('replace', false)} />
        <span className="shrink-0">{t('output_to')}</span>
        <input
          type="text"
          value={out}
          onChange={(e) => onChange('out', e.target.value)}
          disabled={replace}
          placeholder="C:\output"
          className="field-sm flex-1 min-w-[10rem] font-mono disabled:opacity-40"
        />
        <button
          type="button"
          disabled={replace}
          onClick={() => void pickOut()}
          className="btn-outline h-7 px-2 disabled:opacity-40"
          title={t('browse')}
        >
          <FolderOpen size={13} strokeWidth={1.5} />
        </button>
      </label>
      {showBackup && (
        <label className="flex items-center gap-2 text-[13px] cursor-pointer">
          <input
            type="checkbox"
            checked={doBackup}
            onChange={(e) => onChange('do_backup', e.target.checked)}
          />
          {t('enable_backup')}
        </label>
      )}
    </div>
  );
}
