import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Undo2 } from 'lucide-react';
import { useAppStore } from './store/appStore';
import { FolderBar } from './components/FolderBar';
import { FilterBar } from './components/FilterBar';
import { FileTable } from './components/FileTable';
import { PreviewPanel } from './components/PreviewPanel';
import { TaskProgress } from './components/TaskProgress';
import { ToolSidebar, TAB_I18N, type TabKey } from './components/TabLayout';
import type { ScanKind } from './utils/docFormats';
import { CompressPage } from './pages/CompressPage';
import { ConvertPage } from './pages/ConvertPage';
import { DocConvertPage } from './pages/DocConvertPage';
import { RenamePage } from './pages/RenamePage';
import { WatermarkPage } from './pages/WatermarkPage';
import { AiRenamePage } from './pages/AiRenamePage';
import { TrimPage } from './pages/TrimPage';
import { InspectPage } from './pages/InspectPage';
import { NormalizePage } from './pages/NormalizePage';
import { SpritesheetPage } from './pages/SpritesheetPage';
import { GifPage } from './pages/GifPage';
import { api } from './api/client';
import { ResizeHandle } from './components/ResizeHandle';

const LEFT_KEY = 'imgbatch.layout.leftWidth';
const RIGHT_KEY = 'imgbatch.layout.rightWidth';
const PREVIEW_KEY = 'imgbatch.layout.previewWidth';
const LEFT_DEFAULT = 208;
const RIGHT_DEFAULT = 400;
const PREVIEW_DEFAULT = 240;
const LEFT_MIN = 160;
const LEFT_MAX = 320;
const RIGHT_MIN = 300;
const RIGHT_MAX = 720;
const PREVIEW_MIN = 180;
const PREVIEW_MAX = 480;

function readStoredWidth(key: string, def: number, min: number, max: number) {
  try {
    const raw = localStorage.getItem(key);
    if (raw == null) return def;
    const n = parseInt(raw, 10);
    return Number.isNaN(n) ? def : Math.min(max, Math.max(min, n));
  } catch {
    return def;
  }
}

function persistWidth(key: string, val: number) {
  try {
    localStorage.setItem(key, String(Math.round(val)));
  } catch {
    /* ignore write errors (e.g. storage disabled) */
  }
}

export default function App() {
  const { t, i18n } = useTranslation();
  const {
    language,
    loadConfig,
    canUndo,
    refreshUndoStatus,
    setStatusMessage,
    folder,
    refreshFiles,
    setScanKind,
  } = useAppStore();
  const [activeTab, setActiveTab] = useState<TabKey>('compress');
  const [leftWidth, setLeftWidth] = useState(() =>
    readStoredWidth(LEFT_KEY, LEFT_DEFAULT, LEFT_MIN, LEFT_MAX),
  );
  const [rightWidth, setRightWidth] = useState(() =>
    readStoredWidth(RIGHT_KEY, RIGHT_DEFAULT, RIGHT_MIN, RIGHT_MAX),
  );
  const [previewWidth, setPreviewWidth] = useState(() =>
    readStoredWidth(PREVIEW_KEY, PREVIEW_DEFAULT, PREVIEW_MIN, PREVIEW_MAX),
  );

  const TAB_SCAN_KIND: Partial<Record<TabKey, ScanKind>> = {
    doc_convert: 'document',
  };

  useEffect(() => {
    void loadConfig().then(() => {
      void i18n.changeLanguage(language);
    });
  }, []);

  useEffect(() => {
    const kind: ScanKind = TAB_SCAN_KIND[activeTab] ?? 'image';
    setScanKind(kind);
    if (folder) {
      void refreshFiles();
    }
  }, [activeTab]);

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
      case 'doc_convert':
        return <DocConvertPage />;
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
      case 'gif':
        return <GifPage />;
    }
  };

  return (
    <div className="flex flex-col h-screen text-foreground">
      <FolderBar />
      <div className="flex flex-1 min-h-0 overflow-hidden">
        <ToolSidebar activeTab={activeTab} onTabChange={setActiveTab} width={leftWidth} />
        <ResizeHandle
          direction="left"
          getSize={() => leftWidth}
          min={LEFT_MIN}
          max={LEFT_MAX}
          defaultSize={LEFT_DEFAULT}
          onResize={setLeftWidth}
          onResizeEnd={(w) => persistWidth(LEFT_KEY, w)}
        />
        <div className="flex-1 flex flex-col min-w-0 min-h-0">
          <FilterBar />
          <div className="flex flex-1 min-h-0 overflow-hidden">
            <FileTable />
            <ResizeHandle
              direction="right"
              getSize={() => previewWidth}
              min={PREVIEW_MIN}
              max={PREVIEW_MAX}
              defaultSize={PREVIEW_DEFAULT}
              onResize={setPreviewWidth}
              onResizeEnd={(w) => persistWidth(PREVIEW_KEY, w)}
            />
            <PreviewPanel width={previewWidth} />
          </div>
        </div>
        <ResizeHandle
          direction="right"
          getSize={() => rightWidth}
          min={RIGHT_MIN}
          max={RIGHT_MAX}
          defaultSize={RIGHT_DEFAULT}
          onResize={setRightWidth}
          onResizeEnd={(w) => persistWidth(RIGHT_KEY, w)}
        />
        <aside style={{ width: rightWidth }} className="shrink-0 flex flex-col min-h-0 bg-surface">
          <div className="flex items-center justify-between px-3 py-2 border-b border-border shrink-0">
            <span className="text-[13px] font-semibold text-foreground truncate">
              {t(TAB_I18N[activeTab])}
            </span>
            <button
              type="button"
              onClick={() => void handleUndo()}
              disabled={!canUndo}
              title={t('undo_last')}
              className="btn-ghost h-7 text-xs disabled:opacity-35 disabled:cursor-not-allowed shrink-0"
            >
              <Undo2 size={13} strokeWidth={1.5} />
              {t('undo')}
            </button>
          </div>
          <div className="flex-1 overflow-auto min-h-0">{renderPage()}</div>
        </aside>
      </div>
      <TaskProgress />
    </div>
  );
}
