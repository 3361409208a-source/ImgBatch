import { useTranslation } from 'react-i18next';
import {
  ImageDown,
  ArrowLeftRight,
  FileText,
  TextCursorInput,
  Stamp,
  Wand2,
  Crop,
  ScanSearch,
  Ruler,
  LayoutGrid,
  Film,
  Scissors,
  Clapperboard,
  type LucideIcon,
} from 'lucide-react';

export type TabKey =
  | 'compress'
  | 'convert'
  | 'doc_convert'
  | 'rename'
  | 'watermark'
  | 'ai_rename'
  | 'trim'
  | 'inspect'
  | 'normalize'
  | 'spritesheet'
  | 'gif'
  | 'video_anim'
  | 'matting';

const TABS: { key: TabKey; icon: LucideIcon }[] = [
  { key: 'compress', icon: ImageDown },
  { key: 'convert', icon: ArrowLeftRight },
  { key: 'doc_convert', icon: FileText },
  { key: 'rename', icon: TextCursorInput },
  { key: 'watermark', icon: Stamp },
  { key: 'ai_rename', icon: Wand2 },
  { key: 'matting', icon: Scissors },
  { key: 'trim', icon: Crop },
  { key: 'inspect', icon: ScanSearch },
  { key: 'normalize', icon: Ruler },
  { key: 'spritesheet', icon: LayoutGrid },
  { key: 'gif', icon: Film },
  { key: 'video_anim', icon: Clapperboard },
];

export const TAB_I18N: Record<TabKey, string> = {
  compress: 'tab_compress',
  convert: 'tab_format',
  doc_convert: 'tab_doc_convert',
  rename: 'tab_rename',
  watermark: 'tab_watermark',
  ai_rename: 'tab_airename',
  matting: 'tab_matting',
  trim: 'tab_trim',
  inspect: 'tab_inspect',
  normalize: 'tab_normalize',
  spritesheet: 'tab_spritesheet',
  gif: 'tab_gif',
  video_anim: 'tab_video_anim',
};

interface ToolSidebarProps {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
  width?: number;
}

export function ToolSidebar({ activeTab, onTabChange, width }: ToolSidebarProps) {
  const { t } = useTranslation();
  return (
    <nav
      style={width != null ? { width } : undefined}
      className="w-52 shrink-0 flex flex-col gap-0.5 p-2 bg-surface overflow-y-auto"
    >
      {TABS.map(({ key, icon: Icon }) => {
        const active = activeTab === key;
        return (
          <button
            key={key}
            type="button"
            onClick={() => onTabChange(key)}
            className={`flex items-center gap-2 w-full justify-start h-9 px-2.5 text-[13px] font-medium whitespace-nowrap rounded-md
              transition-colors duration-150 cursor-pointer outline-none
              focus-visible:ring-2 focus-visible:ring-ring/30 ${
              active
                ? 'bg-primary/10 text-primary'
                : 'text-[color:var(--color-muted-fg)] hover:bg-muted hover:text-foreground'
            }`}
          >
            <Icon size={15} strokeWidth={1.5} className="shrink-0" />
            {t(TAB_I18N[key])}
          </button>
        );
      })}
    </nav>
  );
}
