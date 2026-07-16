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
