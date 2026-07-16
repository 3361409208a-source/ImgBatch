import { create } from 'zustand';
import { api } from '../api/client';
import { subscribeTask } from '../api/sse';
import type { AppConfig, FileInfo, FilterRequest, TaskCreateRequest } from '../api/types';

interface AppStore {
  folder: string;
  recursive: boolean;
  allFiles: FileInfo[];
  filteredFiles: FileInfo[];
  selectedFile: FileInfo | null;
  previewUrl: string;

  filterName: string;
  filterFormat: string;
  filterSizePreset: string;
  filterMinWidth: string;
  filterMinHeight: string;

  taskRunning: boolean;
  taskProgress: number;
  taskMessage: string;
  taskError: string;
  currentTaskId: string | null;
  lastTaskResult: unknown;
  lastTaskType: string | null;
  canUndo: boolean;
  statusMessage: string;

  config: AppConfig;
  language: 'zh' | 'en';

  setFolder: (f: string) => void;
  setRecursive: (r: boolean) => void;
  refreshFiles: () => Promise<void>;
  applyFilter: () => Promise<void>;
  selectFile: (f: FileInfo | null) => void;
  loadPreview: (path: string) => Promise<void>;
  setFilter: (key: string, value: string) => void;
  startTask: (type: string, params: Record<string, unknown>) => Promise<void>;
  cancelTask: () => Promise<void>;
  loadConfig: () => Promise<void>;
  saveConfig: (config: Record<string, unknown>) => Promise<void>;
  setLanguage: (lang: 'zh' | 'en') => void;
  refreshUndoStatus: () => Promise<void>;
  setStatusMessage: (msg: string) => void;
  clearLastTaskResult: () => void;
}

export const useAppStore = create<AppStore>((set, get) => ({
  folder: '',
  recursive: true,
  allFiles: [],
  filteredFiles: [],
  selectedFile: null,
  previewUrl: '',

  filterName: '',
  filterFormat: 'ALL',
  filterSizePreset: 'all',
  filterMinWidth: '',
  filterMinHeight: '',

  taskRunning: false,
  taskProgress: 0,
  taskMessage: '',
  taskError: '',
  currentTaskId: null,
  lastTaskResult: null,
  lastTaskType: null,
  canUndo: false,
  statusMessage: '',

  config: {} as AppConfig,
  language: 'zh',

  setFolder: (f) => {
    set({ folder: f });
    if (!f) {
      set({ allFiles: [], filteredFiles: [], selectedFile: null, previewUrl: '' });
    }
  },
  setRecursive: (r) => set({ recursive: r }),

  refreshFiles: async () => {
    const { folder, recursive } = get();
    if (!folder) return;
    try {
      set({ taskError: '', statusMessage: '正在扫描…' });
      const res = await api.scan(folder, recursive);
      set({ allFiles: res.files, filteredFiles: res.files, taskError: '' });
      await get().applyFilter();
      await get().refreshUndoStatus();
      set({
        statusMessage:
          res.files.length > 0
            ? `已加载 ${res.files.length} 个文件`
            : '该文件夹下没有图片（可勾选「包含子目录」）',
      });
    } catch (e) {
      const msg = String(e);
      set({ taskError: msg, statusMessage: msg, allFiles: [], filteredFiles: [] });
    }
  },

  applyFilter: async () => {
    const s = get();
    const req: FilterRequest = {
      files: s.allFiles,
      name_query: s.filterName,
      format: s.filterFormat,
      size_preset: s.filterSizePreset,
      min_width: s.filterMinWidth,
      min_height: s.filterMinHeight,
    };
    try {
      const res = await api.filter(req);
      set({ filteredFiles: res.files });
    } catch {
      set({ filteredFiles: s.allFiles });
    }
  },

  selectFile: (f) => {
    set({ selectedFile: f });
    if (f) get().loadPreview(f.path);
    else set({ previewUrl: '' });
  },

  loadPreview: async (path) => {
    try {
      const res = await api.previewThumb(path, 400);
      set({ previewUrl: res.data_url });
    } catch {
      set({ previewUrl: '' });
    }
  },

  setFilter: (key, value) => {
    set({ [key]: value } as Partial<AppStore>);
  },

  startTask: async (type, params) => {
    const s = get();
    if (!s.folder) {
      set({ taskError: 'Select a folder first', statusMessage: 'Select a folder first' });
      return;
    }
    const fileList = s.filteredFiles.map((f) => f.name);
    const req: TaskCreateRequest = {
      type,
      folder: s.folder,
      file_list: fileList,
      params,
    };
    set({
      taskRunning: true,
      taskProgress: 0,
      taskMessage: '',
      taskError: '',
      lastTaskResult: null,
      lastTaskType: type,
      currentTaskId: null,
      statusMessage: '',
    });
    try {
      const res = await api.createTask(req);
      set({ currentTaskId: res.task_id });
      subscribeTask(
        res.task_id,
        (pct, msg) => set({ taskProgress: pct, taskMessage: msg }),
        (status, result) => {
          set({
            taskRunning: false,
            taskProgress: status === 'cancelled' ? get().taskProgress : 100,
            taskError: status === 'error' ? JSON.stringify(result) : '',
            lastTaskResult: result,
            currentTaskId: null,
            taskMessage: status === 'cancelled' ? 'Cancelled' : get().taskMessage,
          });
          if (status === 'done') {
            void get().refreshFiles();
          } else {
            void get().refreshUndoStatus();
          }
        },
      );
    } catch (e) {
      set({ taskRunning: false, taskError: String(e), currentTaskId: null });
    }
  },

  cancelTask: async () => {
    const { currentTaskId } = get();
    if (!currentTaskId) {
      set({ taskRunning: false, taskMessage: 'Cancelled', currentTaskId: null });
      return;
    }
    try {
      await api.cancelTask(currentTaskId);
      set({ taskMessage: 'Cancelling...' });
    } catch (e) {
      set({
        taskRunning: false,
        taskError: String(e),
        currentTaskId: null,
        taskMessage: 'Cancel failed',
      });
    }
  },

  loadConfig: async () => {
    try {
      const cfg = await api.getConfig();
      set({ config: cfg, language: (cfg.language as 'zh' | 'en') || 'zh' });
      await get().refreshUndoStatus();
    } catch (e) {
      console.error('Failed to load config:', e);
    }
  },

  saveConfig: async (config) => {
    try {
      await api.saveConfig(config);
      set({ config: config as AppConfig });
    } catch (e) {
      console.error('Failed to save config:', e);
    }
  },

  setLanguage: (lang) => {
    set({ language: lang });
    const cfg = { ...get().config, language: lang };
    void get().saveConfig(cfg);
  },

  refreshUndoStatus: async () => {
    try {
      const res = await api.undoStatus();
      set({ canUndo: !!res.can_undo });
    } catch {
      set({ canUndo: false });
    }
  },

  setStatusMessage: (msg) => set({ statusMessage: msg }),

  clearLastTaskResult: () => set({ lastTaskResult: null, lastTaskType: null }),
}));
