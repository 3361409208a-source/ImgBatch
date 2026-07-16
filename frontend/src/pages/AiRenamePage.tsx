import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Sparkles, Check, ExternalLink, ClipboardPaste } from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/appStore';
import { buildExternalAiRenamePrompt } from '../utils/aiRenamePrompt';

export function AiRenamePage() {
  const { t } = useTranslation();
  const { startTask, lastTaskResult, lastTaskType, taskRunning, filteredFiles, setStatusMessage } =
    useAppStore();
  const [apiKey, setApiKey] = useState('');
  const [prompt, setPrompt] = useState(() => t('ai_default_user_prompt'));
  const [results, setResults] = useState<Record<string, string>>({});
  const [pasteContent, setPasteContent] = useState('');
  const [parseError, setParseError] = useState('');

  const fileNames = useMemo(() => filteredFiles.map((f) => f.name), [filteredFiles]);

  useEffect(() => {
    if (taskRunning || lastTaskType !== 'ai_rename' || !lastTaskResult) return;
    const payload = lastTaskResult as { results?: Record<string, string> };
    if (payload.results && typeof payload.results === 'object') {
      setResults(payload.results);
    }
  }, [lastTaskResult, lastTaskType, taskRunning]);

  const handleAnalyze = () => {
    if (!apiKey.trim()) {
      alert(t('ai_key_required'));
      return;
    }
    if (fileNames.length === 0) {
      alert(t('ai_no_files'));
      return;
    }
    void startTask('ai_rename', { api_key: apiKey, prompt: prompt.trim() });
  };

  const handleOpenMetaso = async () => {
    if (fileNames.length === 0) {
      alert(t('ai_no_files'));
      return;
    }

    const text = buildExternalAiRenamePrompt(prompt, fileNames, t('ai_default_user_prompt'));
    try {
      await navigator.clipboard.writeText(text);
      setStatusMessage(t('ai_metaso_copied'));
    } catch {
      setStatusMessage(t('ai_metaso_copy_failed'));
    }

    try {
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('open_metaso_assistant');
    } catch (e) {
      try {
        const { invoke } = await import('@tauri-apps/api/core');
        await invoke('open_path', { path: 'https://metaso.cn/' });
        setStatusMessage(t('ai_metaso_browser_fallback'));
      } catch {
        alert(String(e));
      }
    }
  };

  const handleParsePaste = async () => {
    if (fileNames.length === 0) {
      alert(t('ai_no_files'));
      return;
    }
    if (!pasteContent.trim()) {
      setParseError(t('ai_paste_empty'));
      return;
    }

    setParseError('');
    try {
      const res = await api.renameAiParse(pasteContent, fileNames);
      if (res.errors.length > 0) {
        setParseError(res.errors.join('\n'));
      }
      if (Object.keys(res.mapping).length > 0) {
        setResults(res.mapping);
        setStatusMessage(t('ai_parse_ok'));
      }
    } catch (e) {
      setParseError(String(e));
    }
  };

  return (
    <div className="flex flex-col gap-4 p-4 max-w-3xl">
      <p className="text-xs text-[color:var(--color-muted-fg)] leading-relaxed">
        {t('ai_rename_hint')}
      </p>

      <label className="flex flex-col gap-1.5">
        <span className="label-muted">{t('ai_api_key_optional')}</span>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-..."
          className="field font-mono"
        />
      </label>

      <label className="flex flex-col gap-1.5">
        <span className="label-muted">{t('ai_user_prompt_label')}</span>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={3}
          placeholder={t('ai_default_user_prompt')}
          className="field h-auto py-2 resize-none text-xs leading-relaxed"
        />
        <span className="text-[10px] text-[color:var(--color-muted-fg)] leading-relaxed">
          {t('ai_user_prompt_hint')}
        </span>
      </label>

      <div className="flex gap-2 flex-wrap">
        <button
          type="button"
          onClick={handleAnalyze}
          disabled={taskRunning || !apiKey.trim()}
          className="btn-outline disabled:opacity-40"
        >
          <Sparkles size={14} strokeWidth={1.5} />
          {t('ai_analyze')}
        </button>
        <button
          type="button"
          onClick={() => void handleOpenMetaso()}
          disabled={taskRunning || fileNames.length === 0}
          className="btn-outline disabled:opacity-40"
          title={t('ai_metaso_hint')}
        >
          <ExternalLink size={14} strokeWidth={1.5} />
          {t('ai_metaso_open')}
        </button>
        <button
          type="button"
          onClick={() => void startTask('ai_apply', { mapping: results })}
          disabled={Object.keys(results).length === 0 || taskRunning}
          className="btn-cta disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Check size={14} strokeWidth={1.5} />
          {t('apply_ai')}
        </button>
        <button type="button" onClick={() => setResults({})} className="btn-ghost text-xs">
          {t('clear_results')}
        </button>
      </div>

      <div className="rounded-md border border-border bg-[color:var(--color-surface-2)] p-3 flex flex-col gap-2">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <span className="text-xs font-medium">{t('ai_paste_title')}</span>
          <span className="text-[10px] text-[color:var(--color-muted-fg)]">{t('ai_metaso_steps')}</span>
        </div>
        <textarea
          value={pasteContent}
          onChange={(e) => setPasteContent(e.target.value)}
          rows={5}
          placeholder={t('ai_paste_placeholder')}
          className="field h-auto py-2 resize-y text-xs leading-relaxed font-mono"
        />
        <div className="flex gap-2 flex-wrap">
          <button
            type="button"
            onClick={() => void handleParsePaste()}
            disabled={taskRunning || fileNames.length === 0}
            className="btn-outline text-xs disabled:opacity-40"
          >
            <ClipboardPaste size={14} strokeWidth={1.5} />
            {t('ai_parse_paste')}
          </button>
        </div>
        {parseError && (
          <p className="text-xs text-destructive whitespace-pre-wrap">{parseError}</p>
        )}
      </div>

      {Object.keys(results).length > 0 && (
        <div className="max-h-48 overflow-auto border border-border rounded-md p-2 text-xs font-mono bg-[color:var(--color-surface-2)]">
          <div className="text-[10px] text-[color:var(--color-muted-fg)] mb-1">{t('ai_preview')}</div>
          {Object.entries(results).map(([old, newN]) => (
            <div key={old} className="flex gap-2 py-0.5">
              <span className="text-destructive">{old}</span>
              <span className="text-[color:var(--color-muted-fg)]">-&gt;</span>
              <span className="text-primary">{newN}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
