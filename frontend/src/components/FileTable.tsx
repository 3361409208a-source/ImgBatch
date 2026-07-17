import { useTranslation } from 'react-i18next';
import { FolderOpen } from 'lucide-react';
import { useAppStore } from '../store/appStore';

export function FileTable() {
  const { t } = useTranslation();
  const { filteredFiles, selectedFile, selectFile, folder } = useAppStore();

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
                <div className="flex flex-col items-center gap-3 text-[color:var(--color-muted-fg)]">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                    <FolderOpen size={22} strokeWidth={1.5} className="opacity-60" />
                  </div>
                  <p className="text-sm">{t('select_folder_first')}</p>
                  {!folder && (
                    <p className="text-xs opacity-70">点击「浏览」选择图片文件夹</p>
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
