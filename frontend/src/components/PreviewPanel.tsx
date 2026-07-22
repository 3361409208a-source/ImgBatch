import { useTranslation } from 'react-i18next';
import { FileText, Image } from 'lucide-react';
import { useAppStore } from '../store/appStore';

interface PreviewPanelProps {
  width?: number;
}

export function PreviewPanel({ width }: PreviewPanelProps) {
  const { t } = useTranslation();
  const { previewUrl, previewText, previewKind, selectedFile } = useAppStore();
  const hasImage = previewKind === 'image' && !!previewUrl;
  const hasText = previewKind === 'text' && !!previewText;

  return (
    <aside
      style={width != null ? { width } : undefined}
      className="w-60 shrink-0 flex flex-col min-h-0 bg-[color:var(--color-surface-2)] border-l border-border"
    >
      <div className="px-3 py-2 border-b border-border flex items-center justify-between shrink-0 gap-2">
        <span className="label-muted shrink-0">{t('preview')}</span>
        {selectedFile && (
          <span
            className="text-[10px] font-mono text-[color:var(--color-muted-fg)] truncate min-w-0"
            title={selectedFile.name}
          >
            {selectedFile.name}
          </span>
        )}
      </div>
      <div className="flex-1 flex items-center justify-center p-3 min-h-0 overflow-hidden">
        {hasImage ? (
          <div className="w-full h-full flex items-center justify-center rounded-md bg-[repeating-conic-gradient(#e8ecf1_0%_25%,#fff_0%_50%)] bg-[length:12px_12px] border border-border/60 p-2">
            <img
              src={previewUrl}
              alt={selectedFile?.name}
              className="max-w-full max-h-full object-contain shadow-md"
            />
          </div>
        ) : hasText ? (
          <pre className="w-full h-full overflow-auto rounded-md border border-border/60 bg-surface p-2 text-[11px] leading-relaxed whitespace-pre-wrap break-words text-[color:var(--color-fg)] font-mono">
            {previewText}
          </pre>
        ) : (
          <div className="flex flex-col items-center gap-2 font-mono select-none text-center">
            <span className="text-lg tracking-widest text-primary/80 font-bold animate-pulse">
              (◡‿◡✿)
            </span>
            <span className="text-[10px] font-mono tracking-wider text-muted-foreground border border-border/80 px-2.5 py-1 rounded bg-muted/40 shadow-xs">
              [ NO PREVIEW SELECTION ]
            </span>
            <span className="text-[11px] text-muted-foreground/80 mt-0.5 font-mono">
              (っ◕◡角)っ {t('preview')}
            </span>
          </div>
        )}
      </div>
      {selectedFile && (
        <div
          className="px-3 py-2 border-t border-border text-[10px] font-mono text-[color:var(--color-muted-fg)] truncate leading-relaxed shrink-0"
          title={selectedFile.path}
        >
          {selectedFile.path}
        </div>
      )}
    </aside>
  );
}
