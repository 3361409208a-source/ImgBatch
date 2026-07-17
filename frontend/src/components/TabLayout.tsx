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
  | 'gif';

const TABS: { key: TabKey; icon: LucideIcon }[] = [
  { key: 'compress', icon: ImageDown },
  { key: 'convert', icon: ArrowLeftRight },
  { key: 'doc_convert', icon: FileText },
  { key: 'rename', icon: TextCursorInput },
  { key: 'watermark', icon: Stamp },
  { key: 'ai_rename', icon: Wand2 },
  { key: 'trim', icon: Crop },
  { key: 'inspect', icon: ScanSearch },
  { key: 'normalize', icon: Ruler },
  { key: 'spritesheet', icon: LayoutGrid },
  { key: 'gif', icon: Film },
];

const TAB_I18N: Record<TabKey, string> = {
  compress: 'tab_compress',
  convert: 'tab_format',
  doc_convert: 'tab_doc_convert',
  rename: 'tab_rename',
  watermark: 'tab_watermark',
  ai_rename: 'tab_airename',
  trim: 'tab_trim',
  inspect: 'tab_inspect',
  normalize: 'tab_normalize',
  spritesheet: 'tab_spritesheet',
  gif: 'tab_gif',
};

interface TabLayoutProps {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
}

export function TabLayout({ activeTab, onTabChange }: TabLayoutProps) {
  const { t } = useTranslation();
  return (
    <nav className="flex items-center gap-0.5 px-3 py-1.5 bg-surface border-b border-border overflow-x-auto">
      {TABS.map(({ key, icon: Icon }) => {
        const active = activeTab === key;
        return (
          <button
            key={key}
            type="button"
            onClick={() => onTabChange(key)}
            className={`flex items-center gap-1.5 h-8 px-2.5 text-[12px] font-medium whitespace-nowrap rounded-md
              transition-colors duration-150 cursor-pointer outline-none
              focus-visible:ring-2 focus-visible:ring-ring/30 ${
              active
                ? 'bg-primary/10 text-primary'
                : 'text-[color:var(--color-muted-fg)] hover:bg-muted hover:text-foreground'
            }`}
          >
            <Icon size={14} strokeWidth={1.5} />
            {t(TAB_I18N[key])}
          </button>
        );
      })}
    </nav>
  );
}
