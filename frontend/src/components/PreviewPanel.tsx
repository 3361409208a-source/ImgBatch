import { useTranslation } from 'react-i18next';
import { Image } from 'lucide-react';
import { useAppStore } from '../store/appStore';

export function PreviewPanel() {
  const { t } = useTranslation();
  const { previewUrl, selectedFile } = useAppStore();

  return (
    <aside className="w-60 flex flex-col bg-[color:var(--color-surface-2)] border-l border-border shrink-0">
      <div className="px-3 py-2 border-b border-border flex items-center justify-between">
        <span className="label-muted">{t('preview')}</span>
        {selectedFile && (
          <span className="text-[10px] font-mono text-[color:var(--color-muted-fg)] truncate max-w-[8rem]" title={selectedFile.name}>
            {selectedFile.name}
          </span>
        )}
      </div>
      <div className="flex-1 flex items-center justify-center p-3 min-h-0">
        {previewUrl ? (
          <div className="w-full h-full flex items-center justify-center rounded-md bg-[repeating-conic-gradient(#e8ecf1_0%_25%,#fff_0%_50%)] bg-[length:12px_12px] border border-border/60 p-2">
            <img
              src={previewUrl}
              alt={selectedFile?.name}
              className="max-w-full max-h-full object-contain shadow-md"
            />
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 text-[color:var(--color-muted-fg)]">
            <div className="flex h-14 w-14 items-center justify-center rounded-lg border border-dashed border-border bg-surface">
              <Image size={24} strokeWidth={1.25} className="opacity-40" />
            </div>
            <span className="text-[11px]">{t('preview')}</span>
          </div>
        )}
      </div>
      {selectedFile && (
        <div
          className="px-3 py-2 border-t border-border text-[10px] font-mono text-[color:var(--color-muted-fg)] truncate leading-relaxed"
          title={selectedFile.path}
        >
          {selectedFile.path}
        </div>
      )}
    </aside>
  );
}
