import { useState, useEffect } from 'react';
import { Sparkles, Terminal } from 'lucide-react';

const ASCII_LOGO = [
  "  ___               ____   _  _        _     ",
  " |_ _| _ __ ___    | __ ) / \\| |_  ___| |__  ",
  "  | | | '_ ` _ \\   |  _ \\/ _ \\ __|/ __| '_ \\ ",
  "  | | | | | | | |  | |_) / ___ \\ |_| (__| | | |",
  " |___|_| |_| |_|   |____/_/   \\_\\__|\\___|_| |_|",
];

const KAOMOJI_SUB = "(っ◔◡◔)っ ♡ BATCH IMAGE ENGINE v3.0 ♡ (◡‿◡✿)";
const KAOMOJI_SUB2 = "(✿◠‿◠)  HIGH-PERFORMANCE IMAGE SYSTEM  (•̀ᴗ•́)و";

interface SplashScreenProps {
  onFinish?: () => void;
}

export function SplashScreen({ onFinish }: SplashScreenProps) {
  const [lineIndex, setLineIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const [fading, setFading] = useState(false);
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    // 1. Line-by-line typewriter effect
    const lineTimer = setInterval(() => {
      setLineIndex((prev) => {
        if (prev < ASCII_LOGO.length + 2) {
          return prev + 1;
        }
        clearInterval(lineTimer);
        return prev;
      });
    }, 120);

    // 2. Progress bar timer
    const progressTimer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(progressTimer);
          return 100;
        }
        return prev + 4;
      });
    }, 40);

    // 3. Auto dismiss after 1.8 seconds
    const dismissTimer = setTimeout(() => {
      triggerDismiss();
    }, 2000);

    return () => {
      clearInterval(lineTimer);
      clearInterval(progressTimer);
      clearTimeout(dismissTimer);
    };
  }, []);

  const triggerDismiss = () => {
    setFading(true);
    setTimeout(() => {
      setHidden(true);
      onFinish?.();
    }, 500);
  };

  if (hidden) return null;

  return (
    <div
      onClick={triggerDismiss}
      className={`fixed inset-0 z-[100] flex flex-col items-center justify-center bg-slate-950 text-emerald-400 font-mono select-none transition-opacity duration-500 cursor-pointer overflow-hidden ${
        fading ? 'opacity-0 pointer-events-none' : 'opacity-100'
      }`}
    >
      {/* Background Matrix/Cyber Ambient Glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(16,185,129,0.15),transparent_70%)] pointer-events-none" />
      <div className="absolute inset-0 bg-[linear-gradient(to_bottom,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:100%_4px] pointer-events-none opacity-40" />

      <div className="relative z-10 flex flex-col items-center max-w-2xl px-6 py-8 rounded-2xl border border-emerald-500/20 bg-slate-900/80 backdrop-blur-md shadow-[0_0_50px_rgba(16,185,129,0.2)]">
        {/* Terminal Header */}
        <div className="w-full flex items-center justify-between px-3 py-1.5 mb-4 rounded-md border border-emerald-500/30 bg-emerald-950/40 text-[11px] text-emerald-400/80">
          <div className="flex items-center gap-2">
            <Terminal size={13} className="text-emerald-400" />
            <span>ImgBatch.System.Core --v3.0.0</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500/40" />
            <span className="w-2 h-2 rounded-full bg-emerald-500/70" />
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          </div>
        </div>

        {/* ASCII Banner */}
        <div className="font-mono text-[11px] sm:text-xs leading-none tracking-tighter text-emerald-300 drop-shadow-[0_0_10px_rgba(52,211,153,0.7)] text-center my-2 min-h-[90px] flex flex-col justify-center">
          {ASCII_LOGO.slice(0, lineIndex).map((line, idx) => (
            <pre key={idx} className="font-mono leading-[1.15] overflow-hidden whitespace-pre">
              {line}
            </pre>
          ))}
        </div>

        {/* Kaomoji / 艺术颜文字 Lines */}
        <div className="flex flex-col items-center gap-1 mt-3 text-xs sm:text-sm font-semibold tracking-wide text-cyan-300 drop-shadow-[0_0_8px_rgba(6,182,212,0.6)]">
          {lineIndex >= ASCII_LOGO.length && (
            <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
              {KAOMOJI_SUB}
            </div>
          )}
          {lineIndex >= ASCII_LOGO.length + 1 && (
            <div className="text-[11px] text-emerald-400/90 font-mono animate-in fade-in duration-300">
              {KAOMOJI_SUB2}
            </div>
          )}
        </div>

        {/* Loading Progress Bar */}
        <div className="w-full max-w-sm mt-6 space-y-2">
          <div className="flex justify-between items-center text-[10px] tracking-wider font-mono text-emerald-400/80">
            <span className="flex items-center gap-1.5">
              <Sparkles size={11} className="animate-spin text-emerald-400" />
              LOADING SYSTEM ENGINES...
            </span>
            <span className="font-bold text-emerald-300">{progress}%</span>
          </div>
          <div className="h-1.5 w-full bg-emerald-950/80 rounded-full border border-emerald-500/30 p-0.5 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-cyan-400 rounded-full transition-all duration-75 shadow-[0_0_10px_rgba(52,211,153,0.9)]"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Skip Tip */}
        <span className="mt-4 text-[10px] text-emerald-500/60 font-mono tracking-widest uppercase animate-pulse">
          [ Click anywhere to skip ]
        </span>
      </div>
    </div>
  );
}
