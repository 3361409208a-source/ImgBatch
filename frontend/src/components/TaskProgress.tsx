import { useTranslation } from 'react-i18next';
import { Loader2, X } from 'lucide-react';
import { useAppStore } from '../store/appStore';

export function TaskProgress() {
  const { t } = useTranslation();
  const { taskRunning, taskProgress, taskMessage, taskError, cancelTask } = useAppStore();

  if (!taskRunning && !taskError && taskProgress === 0) return null;

  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-surface border-t border-border shadow-[0_-4px_12px_rgba(15,23,42,0.04)]">
      {taskRunning && <Loader2 size={14} strokeWidth={1.5} className="animate-spin text-primary shrink-0" />}
      <div className="flex-1 flex items-center gap-3 min-w-0">
        <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden max-w-md">
          <div
            className="h-full bg-primary rounded-full transition-all duration-300 ease-out"
            style={{ width: `${Math.max(2, taskProgress)}%` }}
          />
        </div>
        <span className="text-[11px] font-mono text-[color:var(--color-muted-fg)] w-9 text-right tabular-nums shrink-0">
          {Math.round(taskProgress)}%
        </span>
        {taskMessage && (
          <span className="text-[12px] text-[color:var(--color-muted-fg)] truncate">{taskMessage}</span>
        )}
        {taskError && (
          <span className="text-[12px] text-destructive truncate" title={taskError}>
            {taskError}
          </span>
        )}
      </div>
      {taskRunning && (
        <button type="button" onClick={() => void cancelTask()} className="btn-danger h-7 text-xs shrink-0">
          <X size={12} strokeWidth={1.5} />
          {t('cancel')}
        </button>
      )}
    </div>
  );
}
