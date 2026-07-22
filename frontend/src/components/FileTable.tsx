import { useTranslation } from 'react-i18next';
import { FolderOpen } from 'lucide-react';
import { useAppStore } from '../store/appStore';

export function FileTable() {
  const { t } = useTranslation();
  const { filteredFiles, selectedFile, selectFile, folder, scanKind } = useAppStore();
  const isDoc = scanKind === 'document';

  const openFile = async (path: string) => {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('open_path', { path });
    } catch (e) {
      console.error('open_path failed', e);
    }
  };

  return (
    <div className="flex-1 min-h-0 overflow-auto bg-surface min-w-0">
      <table className="w-full text-[13px] border-collapse">
        <thead className="sticky top-0 z-10">
          <tr className="bg-[color:var(--color-surface-2)] border-b border-border text-left">
            <th className="px-3 py-2 label-muted font-medium">{t('col_name')}</th>
            <th className="px-3 py-2 label-muted font-medium w-24">{t('col_size')}</th>
            <th className="px-3 py-2 label-muted font-medium w-28">{t('col_dim')}</th>
            <th className="px-3 py-2 label-muted font-medium w-16">{t('col_fmt')}</th>
          </tr>
        </thead>
        <tbody>
          {filteredFiles.map((file) => {
            const active = selectedFile?.path === file.path;
            return (
              <tr
                key={file.path}
                onClick={() => selectFile(file)}
                onDoubleClick={() => void openFile(file.path)}
                className={`border-b border-border/70 cursor-pointer transition-colors duration-100 h-9 ${
                  active
                    ? 'bg-primary/10 text-foreground'
                    : 'hover:bg-muted/80'
                }`}
              >
                <td className={`px-3 truncate max-w-[20rem] ${active ? 'font-medium' : ''}`} title={file.name}>
                  {active && (
                    <span className="inline-block w-0.5 h-3 bg-primary rounded-full mr-2 align-middle" />
                  )}
                  {file.name}
                </td>
                <td className="px-3 font-mono text-[11px] text-[color:var(--color-muted-fg)] tabular-nums">
                  {file.size_str}
                </td>
                <td className="px-3 font-mono text-[11px] text-[color:var(--color-muted-fg)] tabular-nums">
                  {file.dimensions}
                </td>
                <td className="px-3">
                  <span className="inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium uppercase tracking-wide bg-muted text-[color:var(--color-muted-fg)]">
                    {file.format}
                  </span>
                </td>
              </tr>
            );
          })}
          {filteredFiles.length === 0 && (
            <tr>
              <td colSpan={4} className="px-3 py-16">
                <div className="flex flex-col items-center gap-2 font-mono select-none text-center">
                  <span className="text-xl tracking-widest text-primary/80 font-bold animate-pulse">
                    ( ° ▽ °;)
                  </span>
                  <span className="text-[11px] font-mono tracking-wider text-muted-foreground border border-border/80 px-3 py-1 rounded-md bg-muted/40 shadow-xs">
                    [ NO FILES FOUND IN TARGET ]
                  </span>
                  <p className="text-xs text-muted-foreground mt-1">
                    (っ˘з(˘⌣˘ ) {t('select_folder_first')}
                  </p>
                  {!folder && (
                    <p className="text-[11px] text-muted-foreground/70 font-mono">
                      {isDoc ? t('browse_doc_hint') : t('browse_image_hint')}
                    </p>
                  )}
                </div>
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
