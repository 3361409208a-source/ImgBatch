import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Play } from 'lucide-react';
import { useAppStore } from '../store/appStore';

export function InspectPage() {
  const { t } = useTranslation();
  const { startTask, lastTaskResult, lastTaskType, taskRunning } = useAppStore();
  const [results, setResults] = useState<Record<string, unknown>[]>([]);

  useEffect(() => {
    if (taskRunning || lastTaskType !== 'inspect' || !lastTaskResult) return;
    const payload = lastTaskResult as { results?: Record<string, unknown>[] };
    if (Array.isArray(payload.results)) {
      setResults(payload.results);
    }
  }, [lastTaskResult, lastTaskType, taskRunning]);

  return (
    <div className="flex flex-col gap-4 p-4 max-w-3xl">
      <p className="text-sm text-[color:var(--color-muted-fg)]">
        {t('start_inspect')}（仅 PNG）
      </p>
      <button
        type="button"
        onClick={() => void startTask('inspect', {})}
        disabled={taskRunning}
        className="btn-cta w-fit disabled:opacity-40"
      >
        <Play size={14} strokeWidth={1.75} />
        {t('start_inspect')}
      </button>
      {results.length > 0 && (
        <div className="overflow-auto border border-border rounded-md">
          <table className="w-full text-xs font-mono">
            <thead className="bg-muted text-[color:var(--color-muted-fg)]">
              <tr>
                <th className="px-2 py-1 text-left">Name</th>
                <th className="px-2 py-1">Canvas</th>
                <th className="px-2 py-1">Content</th>
                <th className="px-2 py-1">L</th>
                <th className="px-2 py-1">R</th>
                <th className="px-2 py-1">T</th>
                <th className="px-2 py-1">B</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={i} className="border-b border-border">
                  <td className="px-2 py-1 truncate max-w-xs">{r.name as string}</td>
                  <td className="px-2 py-1">{r.canvas as string}</td>
                  <td className="px-2 py-1">{r.content as string}</td>
                  <td className="px-2 py-1">{r.left_pad as string}</td>
                  <td className="px-2 py-1">{r.right_pad as string}</td>
                  <td className="px-2 py-1">{r.top_pad as string}</td>
                  <td className="px-2 py-1">{r.bot_pad as string}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
