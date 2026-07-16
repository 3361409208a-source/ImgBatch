import {
  Archive,
  ArrowRight,
  Bot,
  Crop,
  Download,
  FileImage,
  FolderOpen,
  Github,
  Image,
  Layers,
  Menu,
  MousePointerClick,
  Ruler,
  ScanSearch,
  Sparkles,
  Type,
  X,
  Zap,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

const iconMap: Record<string, LucideIcon> = {
  compress: Archive,
  convert: Image,
  rename: Type,
  watermark: Layers,
  ai: Bot,
  trim: Crop,
  inspect: ScanSearch,
  normalize: Ruler,
  desktop: Sparkles,
  context: MousePointerClick,
  quick: Zap,
  backup: FolderOpen,
};

export function FeatureIcon({ name, className }: { name: string; className?: string }) {
  const Icon = iconMap[name] ?? FileImage;
  return <Icon className={className} aria-hidden />;
}

export { ArrowRight, Download, Github, Menu, X };
