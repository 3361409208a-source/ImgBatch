import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Sparkles, Check } from 'lucide-react';
import { useAppStore } from '../store/appStore';

const DEFAULT_PROMPT =
  'Please analyze the following image filenames and generate a concise English filename (with extension) for each, e.g. player_name-position-country.jpg. Return JSON array only.';

export function AiRenamePage() {
  const { t } = useTranslation();
  const { startTask, lastTaskResult, lastTaskType, taskRunning } = useAppStore();
  const [apiKey, setApiKey] = useState('');
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [results, setResults] = useState<Record<string, string>>({});

  useEffect(() => {
    if (taskRunning || lastTaskType !== 'ai_rename' || !lastTaskResult) return;
    const payload = lastTaskResult as { results?: Record<string, string> };
    if (payload.results && typeof payload.results === 'object') {
      setResults(payload.results);
    }
  }, [lastTaskResult, lastTaskType, taskRunning]);

  const handleAnalyze = () => {
    if (!apiKey.trim()) {
      alert('Please enter API Key');
      return;
    }
    void startTask('ai_rename', { api_key: apiKey, prompt });
  };

  return (
    <div className="flex flex-col gap-4 p-4 max-w-3xl">
      <label className="flex flex-col gap-1.5">
        <span className="label-muted">DeepSeek API Key</span>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-..."
          className="field font-mono"
        />
      </label>
      <label className="flex flex-col gap-1.5">
        <span className="label-muted">{t('prompt')}</span>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={4}
          className="field h-auto py-2 resize-none text-xs leading-relaxed"
        />
      </label>
      <div className="flex gap-2 flex-wrap">
        <button type="button" onClick={handleAnalyze} disabled={taskRunning} className="btn-outline disabled:opacity-40">
          <Sparkles size={14} strokeWidth={1.5} />
          {t('ai_analyze')}
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
          {t('clear_results') || 'Clear'}
        </button>
      </div>
      {Object.keys(results).length > 0 && (
        <div className="max-h-48 overflow-auto border border-border rounded-md p-2 text-xs font-mono bg-[color:var(--color-surface-2)]">
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
