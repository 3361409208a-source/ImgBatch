import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Undo2 } from 'lucide-react';
import { useAppStore } from './store/appStore';
import { FolderBar } from './components/FolderBar';
import { FilterBar } from './components/FilterBar';
import { FileTable } from './components/FileTable';
import { PreviewPanel } from './components/PreviewPanel';
import { TaskProgress } from './components/TaskProgress';
import { TabLayout, type TabKey } from './components/TabLayout';
import { CompressPage } from './pages/CompressPage';
import { ConvertPage } from './pages/ConvertPage';
import { RenamePage } from './pages/RenamePage';
import { WatermarkPage } from './pages/WatermarkPage';
import { AiRenamePage } from './pages/AiRenamePage';
import { TrimPage } from './pages/TrimPage';
import { InspectPage } from './pages/InspectPage';
import { NormalizePage } from './pages/NormalizePage';
import { SpritesheetPage } from './pages/SpritesheetPage';
import { api } from './api/client';

export default function App() {
  const { t, i18n } = useTranslation();
  const {
    language,
    loadConfig,
    refreshFiles,
    canUndo,
    refreshUndoStatus,
    setStatusMessage,
    statusMessage,
  } = useAppStore();
  const [activeTab, setActiveTab] = useState<TabKey>('compress');

  useEffect(() => {
    void loadConfig().then(() => {
      void i18n.changeLanguage(language);
    });
  }, []);

  useEffect(() => {
    void i18n.changeLanguage(language);
  }, [language, i18n]);

  const handleUndo = async () => {
    try {
      const res = await api.undo();
      if (res.success) {
        setStatusMessage(t('undo_done', { op: res.message || '' }));
        await refreshFiles();
      } else {
        setStatusMessage(t('no_undo'));
      }
      await refreshUndoStatus();
    } catch (e) {
      setStatusMessage(String(e));
    }
  };

  const renderPage = () => {
    switch (activeTab) {
      case 'compress':
        return <CompressPage />;
      case 'convert':
        return <ConvertPage />;
      case 'rename':
        return <RenamePage />;
      case 'watermark':
        return <WatermarkPage />;
      case 'ai_rename':
        return <AiRenamePage />;
      case 'trim':
        return <TrimPage />;
      case 'inspect':
        return <InspectPage />;
      case 'normalize':
        return <NormalizePage />;
      case 'spritesheet':
        return <SpritesheetPage />;
    }
  };

  return (
    <div className="flex flex-col h-screen text-foreground">
      <FolderBar />
      <FilterBar />
      <div className="flex flex-[1.35] overflow-hidden min-h-0 panel border-x-0 rounded-none">
        <FileTable />
        <PreviewPanel />
      </div>
      <TabLayout activeTab={activeTab} onTabChange={setActiveTab} />
      <div className="flex-1 overflow-auto relative min-h-[180px] bg-surface">
        <div className="absolute top-2.5 right-4 z-10 flex items-center gap-2">
          {statusMessage && (
            <span
              className="text-[11px] text-[color:var(--color-muted-fg)] max-w-xs truncate"
              title={statusMessage}
            >
              {statusMessage}
            </span>
          )}
          <button
            type="button"
            onClick={() => void handleUndo()}
            disabled={!canUndo}
            title={t('undo_last')}
            className="btn-ghost h-7 text-xs disabled:opacity-35 disabled:cursor-not-allowed"
          >
            <Undo2 size={13} strokeWidth={1.5} />
            {t('undo')}
          </button>
        </div>
        {renderPage()}
      </div>
      <TaskProgress />
    </div>
  );
}
