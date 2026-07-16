import type {
  AppConfig,
  CompressEstimateResponse,
  FileInfo,
  FilterRequest,
  PreviewResponse,
  RenamePreviewResponse,
  ScanResponse,
  TaskCreateRequest,
  TaskCreateResponse,
  TaskStatus,
  UndoResponse,
} from './types';

let cachedBase: string | null = null;

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

export function resetApiBaseCache() {
  cachedBase = null;
}

/** Resolve API base URL; wait for sidecar. */
export async function getApiBase(force = false): Promise<string> {
  if (!force && cachedBase) return cachedBase;

  let lastErr = 'API not ready';
  for (let i = 0; i < 40; i++) {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const base = await invoke<string>('get_api_base_url');
      const res = await fetch(`${base}/health`);
      if (res.ok) {
        cachedBase = base;
        return base;
      }
      lastErr = `health ${res.status}`;
    } catch (e) {
      lastErr = String(e);
      if (i === 5) {
        try {
          const res = await fetch('http://127.0.0.1:18555/health');
          if (res.ok) {
            cachedBase = 'http://127.0.0.1:18555';
            return cachedBase;
          }
        } catch {
          /* ignore */
        }
      }
    }
    await sleep(250);
  }
  throw new Error(`API sidecar not ready: ${lastErr}`);
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  retried = false,
): Promise<T> {
  const base = await getApiBase(retried);
  let res: Response;
  try {
    res = await fetch(`${base}${path}`, {
      method,
      headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (e) {
    // Sidecar likely restarted on a new port — clear cache and retry once
    if (!retried) {
      resetApiBaseCache();
      return request<T>(method, path, body, true);
    }
    throw new Error(`Network error: ${e}`);
  }

  if (!res.ok) {
    // Stale port often returns connection reset earlier; 502/404 from wrong service
    if (!retried && (res.status >= 500 || res.status === 404)) {
      resetApiBaseCache();
      return request<T>(method, path, body, true);
    }
    throw new Error(await res.text());
  }
  return res.json();
}

export async function apiGet<T>(path: string): Promise<T> {
  return request<T>('GET', path);
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  return request<T>('POST', path, body);
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  return request<T>('PUT', path, body);
}

export async function apiDelete<T>(path: string, body?: unknown): Promise<T> {
  return request<T>('DELETE', path, body);
}

export const api = {
  health: () => apiGet<{ ok: boolean }>('/health'),
  getConfig: () => apiGet<AppConfig>('/config'),
  saveConfig: (config: Record<string, unknown>) =>
    apiPut<{ ok: boolean }>('/config', config),
  scan: (folder: string, recursive: boolean) =>
    apiPost<ScanResponse>('/scan', { folder, recursive }),
  filter: (req: FilterRequest) =>
    apiPost<{ files: FileInfo[] }>('/filter', req),
  compressEstimate: (files: FileInfo[], quality: number, resize_pct: number) =>
    apiPost<CompressEstimateResponse>('/compress/estimate', { files, quality, resize_pct }),
  renamePreview: (req: Record<string, unknown>) =>
    apiPost<RenamePreviewResponse>('/rename/preview', req),
  previewThumb: (path: string, max_size?: number) =>
    apiPost<PreviewResponse>('/preview/thumb', { path, max_size: max_size ?? 300 }),
  createTask: (req: TaskCreateRequest) =>
    apiPost<TaskCreateResponse>('/tasks', req),
  getTask: (taskId: string) =>
    apiGet<TaskStatus>(`/tasks/${taskId}`),
  cancelTask: (taskId: string) =>
    apiDelete<{ ok: boolean }>(`/tasks/${taskId}`),
  listBackups: (folder: string) =>
    apiGet<{ backups: string[] }>(`/backups?folder=${encodeURIComponent(folder)}`),
  restoreBackup: (backupDir: string, folder: string) =>
    apiPost<{ restored: number }>('/backups/restore', { backup_dir: backupDir, folder }),
  clearBackups: (backups: string[]) =>
    apiDelete<{ deleted: number }>('/backups', { backups }),
  undo: () => apiPost<UndoResponse>('/undo', {}),
  undoStatus: () => apiGet<{ can_undo: boolean }>('/undo'),
};
