import { useTranslation } from 'react-i18next';
import { Sparkles, X } from 'lucide-react';
import { useAppStore } from '../store/appStore';

export function TaskProgress() {
  const { t } = useTranslation();
  const { taskRunning, taskProgress, taskMessage, taskError, cancelTask } = useAppStore();

  if (!taskRunning && !taskError && taskProgress === 0) return null;

  const getKaomoji = (pct: number) => {
    if (pct >= 100) return '(✿◠‿◠) COMPLETE!';
    if (pct >= 75) return '(っ◕◡角)っ ALMOST...';
    if (pct >= 40) return '( •̀ᴗ•́)o PROCESSING...';
    return '( •̀_•| ) WORKING...';
  };

  const kaomoji = getKaomoji(taskProgress);

  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-slate-900 text-emerald-400 border-t border-emerald-500/20 font-mono shadow-[0_-4px_16px_rgba(16,185,129,0.08)]">
      {taskRunning && <Sparkles size={14} className="animate-spin text-emerald-400 shrink-0" />}
      
      <div className="flex items-center gap-2 text-xs font-semibold shrink-0 text-cyan-300 drop-shadow-[0_0_6px_rgba(6,182,212,0.6)]">
        <span>{kaomoji}</span>
      </div>

      <div className="flex-1 flex items-center gap-3 min-w-0">
        <div className="flex-1 h-2 bg-emerald-950/80 rounded-full overflow-hidden border border-emerald-500/30 max-w-md p-0.5">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 to-cyan-400 rounded-full transition-all duration-300 ease-out shadow-[0_0_8px_rgba(52,211,153,0.8)]"
            style={{ width: `${Math.max(2, taskProgress)}%` }}
          />
        </div>
        <span className="text-[11px] font-mono text-emerald-300 w-10 text-right tabular-nums shrink-0 font-bold">
          {Math.round(taskProgress)}%
        </span>
        {taskMessage && (
          <span className="text-[11px] text-emerald-200/90 truncate font-mono">{taskMessage}</span>
        )}
        {taskError && (
          <span className="text-[11px] text-rose-400 truncate font-mono" title={taskError}>
            (x_x) {taskError}
          </span>
        )}
      </div>
      {taskRunning && (
        <button type="button" onClick={() => void cancelTask()} className="btn-danger h-7 text-xs px-2.5 shrink-0 gap-1 font-mono">
          <X size={12} strokeWidth={1.5} />
          {t('cancel')}
        </button>
      )}
    </div>
  );
}
