export interface FileInfo {
  name: string;
  path: string;
  size: number;
  size_str: string;
  dimensions: string;
  format: string;
}

export interface ScanResponse {
  files: FileInfo[];
}

export interface FilterRequest {
  files: FileInfo[];
  name_query?: string;
  format?: string;
  size_preset?: string;
  size_min_kb?: string;
  size_max_kb?: string;
  min_width?: string;
  min_height?: string;
}

export interface CompressEstimateResponse {
  total_before: number;
  total_after: number;
}

export interface RenamePreviewResponse {
  mapping: Record<string, string>;
}

export interface AiRenameParseResponse {
  mapping: Record<string, string>;
  errors: string[];
}

export interface TaskCreateRequest {
  type: string;
  folder: string;
  file_list: string[];
  params: Record<string, unknown>;
}

export interface TaskCreateResponse {
  task_id: string;
}

export interface TaskStatus {
  task_id: string;
  done: boolean;
  result: Record<string, unknown> | null;
  error: string | null;
}

export interface PreviewResponse {
  data_url: string;
  kind?: 'image' | 'text' | 'none';
  text?: string;
}

export interface UndoResponse {
  success: boolean;
  message: string;
}

export interface AppConfig {
  language: string;
  last_folder: string;
  [key: string]: unknown;
}

export interface ConvertTarget {
  ext: string;
  label: string;
  group: string;
  supports_quality: boolean;
}

export interface ConvertPreset {
  id: string;
  label: string;
  target_fmt: string;
  quality: number | null;
  hint: string;
}

export interface ConvertCatalogResponse {
  targets: ConvertTarget[];
  presets: ConvertPreset[];
  features: {
    heic_input: boolean;
    avif_output: boolean;
  };
}

export interface DocTarget {
  ext: string;
  label: string;
  group: string;
}

export interface DocPreset {
  id: string;
  label: string;
  target_fmt: string;
  hint: string;
}

export interface DocCatalogResponse {
  targets: DocTarget[];
  presets: DocPreset[];
  features: {
    libreoffice: boolean;
    pymupdf: boolean;
  };
  inputs: string[];
}

export interface ExtensionItem {
  id: string;
  name: string;
  name_en: string;
  description: string;
  description_en: string;
  download_url: string;
  install_dir?: string;
  size_hint: string;
  size_hint_en: string;
  installed: boolean;
  install_path: string | null;
  unlocks: string[];
  unlocks_en: string[];
}

export interface ExtensionInstallStatus {
  running: boolean;
  progress: number;
  message: string;
  error: string | null;
  install_path: string | null;
}

export interface ExtensionCatalogResponse {
  extensions: ExtensionItem[];
  locked_count: number;
  unlocked_count: number;
  total_count: number;
  install?: ExtensionInstallStatus | null;
}

export interface ExtensionInstallResponse {
  started: boolean;
  already_installed: boolean;
  install_path?: string | null;
}
