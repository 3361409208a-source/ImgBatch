import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Play, Info } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { OutputOptions } from '../components/OutputOptions';
import { api } from '../api/client';

type GifMode =
  | 'optimize'
  | 'resize'
  | 'speed'
  | 'set_fps'
  | 'loop'
  | 'reverse'
  | 'extract'
  | 'compose'
  | 'crop'
  | 'trim'
  | 'rotate'
  | 'flip'
  | 'frame_step'
  | 'merge'
  | 'watermark'
  | 'reduce_colors'
  | 'set_delay';

interface GifMeta {
  path: string;
  is_animated: boolean;
  n_frames: number;
  duration_ms: number;
  avg_fps: number;
  loop: number;
}

const MODES: GifMode[] = [
  'optimize',
  'resize',
  'reduce_colors',
  'speed',
  'set_fps',
  'set_delay',
  'loop',
  'reverse',
  'frame_step',
  'trim',
  'crop',
  'rotate',
  'flip',
  'watermark',
  'extract',
  'compose',
  'merge',
];

function requireOut(replace: boolean, out: string, mode: GifMode): boolean {
  if (mode === 'compose' || mode === 'merge') return true;
  if (!replace && !out.trim()) {
    alert('请设置输出目录（不替换原文件时）');
    return false;
  }
  return true;
}

export function GifPage() {
  const { t } = useTranslation();
  const { startTask, filteredFiles, folder, selectedFile } = useAppStore();
  const [mode, setMode] = useState<GifMode>('optimize');
  const [replace, setReplace] = useState(true);
  const [doBackup, setDoBackup] = useState(true);
  const [out, setOut] = useState('');

  const [resizePct, setResizePct] = useState(100);
  const [maxWidth, setMaxWidth] = useState(0);
  const [maxHeight, setMaxHeight] = useState(0);
  const [colors, setColors] = useState(256);
  const [speedFactor, setSpeedFactor] = useState(1);
  const [targetFps, setTargetFps] = useState(10);
  const [frameDelay, setFrameDelay] = useState(100);
  const [loopCount, setLoopCount] = useState(0);
  const [frameStep, setFrameStep] = useState(2);
  const [padding, setPadding] = useState(4);
  const [alphaThreshold, setAlphaThreshold] = useState(28);
  const [autoTrim, setAutoTrim] = useState(true);
  const [cropLeft, setCropLeft] = useState(0);
  const [cropTop, setCropTop] = useState(0);
  const [cropRight, setCropRight] = useState(0);
  const [cropBottom, setCropBottom] = useState(0);
  const [angle, setAngle] = useState(90);
  const [flipDir, setFlipDir] = useState<'horizontal' | 'vertical'>('horizontal');
  const [wmText, setWmText] = useState('© ImgBatch');
  const [wmOpacity, setWmOpacity] = useState(50);
  const [wmPosition, setWmPosition] = useState('bottom-right');
  const [composeDuration, setComposeDuration] = useState(100);
  const [outputName, setOutputName] = useState('');

  const [gifMeta, setGifMeta] = useState<GifMeta | null>(null);

  const gifFiles = useMemo(
    () => filteredFiles.filter((f) => f.name.toLowerCase().endsWith('.gif')),
    [filteredFiles],
  );

  const probePath = selectedFile?.path || gifFiles[0]?.path;

  useEffect(() => {
    if (!probePath?.toLowerCase().endsWith('.gif')) {
      setGifMeta(null);
      return;
    }
    void api.gifInfo([probePath]).then((res) => {
      setGifMeta(res.items[0] ?? null);
    }).catch(() => setGifMeta(null));
  }, [probePath]);

  const buildParams = (): Record<string, unknown> => {
    const base: Record<string, unknown> = {
      mode,
      do_backup: doBackup,
      replace,
      out: replace ? null : out,
      colors,
      optimize: true,
    };

    switch (mode) {
      case 'optimize':
        return { ...base, resize_pct: resizePct, max_width: maxWidth, max_height: maxHeight };
      case 'resize':
        return { ...base, resize_pct: resizePct, max_width: maxWidth, max_height: maxHeight };
      case 'reduce_colors':
        return { ...base, colors, resize_pct: resizePct };
      case 'speed':
        return { ...base, speed_factor: speedFactor };
      case 'set_fps':
        return { ...base, target_fps: targetFps };
      case 'set_delay':
        return { ...base, frame_delay: frameDelay };
      case 'loop':
        return { ...base, loop: loopCount };
      case 'reverse':
        return base;
      case 'frame_step':
        return { ...base, frame_step: frameStep };
      case 'trim':
        return { ...base, auto_trim: true, padding, alpha_threshold: alphaThreshold };
      case 'crop':
        return {
          ...base,
          auto_trim: autoTrim,
          padding,
          alpha_threshold: alphaThreshold,
          left: cropLeft,
          top: cropTop,
          right: cropRight || undefined,
          bottom: cropBottom || undefined,
        };
      case 'rotate':
        return { ...base, angle };
      case 'flip':
        return { ...base, direction: flipDir };
      case 'watermark':
        return {
          ...base,
          watermark: {
            type: 'text',
            text: wmText,
            opacity: wmOpacity,
            position: wmPosition,
          },
        };
      case 'extract':
        return base;
      case 'compose':
        return {
          ...base,
          mode: 'compose',
          frame_duration: composeDuration,
          loop: loopCount,
          output: outputName || `${folder}\\animation.gif`,
          replace: true,
        };
      case 'merge':
        return {
          ...base,
          mode: 'merge',
          output: outputName || `${folder}\\merged.gif`,
          replace: true,
        };
      default:
        return base;
    }
  };

  const handleStart = () => {
    if (mode === 'compose') {
      if (filteredFiles.length < 2) {
        alert(t('gif_compose_need_two'));
        return;
      }
    } else if (mode === 'merge') {
      if (gifFiles.length < 2) {
        alert(t('gif_merge_need_two'));
        return;
      }
    } else if (gifFiles.length === 0) {
      alert(t('gif_no_files'));
      return;
    }

    if (!requireOut(replace, out, mode)) return;
    void startTask('gif_edit', buildParams());
  };

  const inputCls =
    'px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none';

  return (
    <div className="flex flex-col gap-4 p-4 max-w-4xl">
      <div className="flex items-start gap-4 flex-wrap">
        <label className="flex flex-col gap-1 text-sm min-w-[180px]">
          <span className="text-muted-foreground">{t('gif_mode')}</span>
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value as GifMode)}
            className={`${inputCls} cursor-pointer`}
          >
            {MODES.map((m) => (
              <option key={m} value={m}>
                {t(`gif_mode_${m}`)}
              </option>
            ))}
          </select>
        </label>

        {gifMeta && (
          <div className="flex items-start gap-2 text-xs text-[color:var(--color-muted-fg)] bg-[color:var(--color-muted)]/25 rounded-md px-3 py-2">
            <Info size={14} className="shrink-0 mt-0.5" />
            <div>
              <div>{t('gif_meta_frames', { n: gifMeta.n_frames })}</div>
              <div>{t('gif_meta_duration', { ms: gifMeta.duration_ms, fps: gifMeta.avg_fps })}</div>
              <div>{t('gif_meta_loop', { loop: gifMeta.loop })}</div>
            </div>
          </div>
        )}
      </div>

      <p className="text-xs text-[color:var(--color-muted-fg)] -mt-2">{t(`gif_hint_${mode}`)}</p>

      {(mode === 'optimize' || mode === 'resize' || mode === 'reduce_colors') && (
        <div className="flex items-center gap-4 flex-wrap">
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted-foreground">{t('resize')}</span>
            <input type="number" value={resizePct} min={1} max={100} onChange={(e) => setResizePct(Number(e.target.value))} className={`w-20 ${inputCls}`} />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted-foreground">{t('gif_max_width')}</span>
            <input type="number" value={maxWidth} min={0} onChange={(e) => setMaxWidth(Number(e.target.value))} className={`w-24 ${inputCls}`} />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted-foreground">{t('gif_max_height')}</span>
            <input type="number" value={maxHeight} min={0} onChange={(e) => setMaxHeight(Number(e.target.value))} className={`w-24 ${inputCls}`} />
          </label>
          {(mode === 'optimize' || mode === 'reduce_colors') && (
            <label className="flex flex-col gap-1 text-sm">
              <span className="text-muted-foreground">{t('gif_colors')}</span>
              <input type="number" value={colors} min={2} max={256} onChange={(e) => setColors(Number(e.target.value))} className={`w-20 ${inputCls}`} />
            </label>
          )}
        </div>
      )}

      {mode === 'speed' && (
        <label className="flex flex-col gap-1 text-sm w-48">
          <span className="text-muted-foreground">{t('gif_speed_factor')}</span>
          <input type="number" step={0.1} value={speedFactor} min={0.1} max={10} onChange={(e) => setSpeedFactor(Number(e.target.value))} className={inputCls} />
        </label>
      )}

      {mode === 'set_fps' && (
        <label className="flex flex-col gap-1 text-sm w-48">
          <span className="text-muted-foreground">{t('gif_target_fps')}</span>
          <input type="number" step={0.5} value={targetFps} min={0.5} max={60} onChange={(e) => setTargetFps(Number(e.target.value))} className={inputCls} />
        </label>
      )}

      {mode === 'set_delay' && (
        <label className="flex flex-col gap-1 text-sm w-48">
          <span className="text-muted-foreground">{t('gif_frame_delay')}</span>
          <input type="number" value={frameDelay} min={10} max={10000} onChange={(e) => setFrameDelay(Number(e.target.value))} className={inputCls} />
        </label>
      )}

      {(mode === 'loop' || mode === 'compose') && (
        <label className="flex flex-col gap-1 text-sm w-56">
          <span className="text-muted-foreground">{t('gif_loop_count')}</span>
          <input type="number" value={loopCount} min={0} onChange={(e) => setLoopCount(Number(e.target.value))} className={inputCls} />
          <span className="text-[10px] text-[color:var(--color-muted-fg)]">{t('gif_loop_hint')}</span>
        </label>
      )}

      {mode === 'frame_step' && (
        <label className="flex flex-col gap-1 text-sm w-48">
          <span className="text-muted-foreground">{t('gif_frame_step')}</span>
          <input type="number" value={frameStep} min={2} max={20} onChange={(e) => setFrameStep(Number(e.target.value))} className={inputCls} />
        </label>
      )}

      {(mode === 'trim' || mode === 'crop') && (
        <div className="flex items-center gap-4 flex-wrap">
          {mode === 'crop' && (
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={autoTrim} onChange={(e) => setAutoTrim(e.target.checked)} className="accent-primary" />
              {t('gif_auto_trim')}
            </label>
          )}
          {!autoTrim && mode === 'crop' && (
            <>
              <label className="flex flex-col gap-1 text-sm"><span className="text-muted-foreground">L</span><input type="number" value={cropLeft} onChange={(e) => setCropLeft(Number(e.target.value))} className={`w-16 ${inputCls}`} /></label>
              <label className="flex flex-col gap-1 text-sm"><span className="text-muted-foreground">T</span><input type="number" value={cropTop} onChange={(e) => setCropTop(Number(e.target.value))} className={`w-16 ${inputCls}`} /></label>
              <label className="flex flex-col gap-1 text-sm"><span className="text-muted-foreground">R</span><input type="number" value={cropRight} onChange={(e) => setCropRight(Number(e.target.value))} className={`w-16 ${inputCls}`} placeholder="auto" /></label>
              <label className="flex flex-col gap-1 text-sm"><span className="text-muted-foreground">B</span><input type="number" value={cropBottom} onChange={(e) => setCropBottom(Number(e.target.value))} className={`w-16 ${inputCls}`} placeholder="auto" /></label>
            </>
          )}
          <label className="flex flex-col gap-1 text-sm"><span className="text-muted-foreground">{t('padding')}</span><input type="number" value={padding} min={0} onChange={(e) => setPadding(Number(e.target.value))} className={`w-16 ${inputCls}`} /></label>
          <label className="flex flex-col gap-1 text-sm"><span className="text-muted-foreground">{t('alpha_threshold')}</span><input type="number" value={alphaThreshold} min={0} max={255} onChange={(e) => setAlphaThreshold(Number(e.target.value))} className={`w-16 ${inputCls}`} /></label>
        </div>
      )}

      {mode === 'rotate' && (
        <label className="flex flex-col gap-1 text-sm w-40">
          <span className="text-muted-foreground">{t('gif_angle')}</span>
          <select value={angle} onChange={(e) => setAngle(Number(e.target.value))} className={`${inputCls} cursor-pointer`}>
            <option value={90}>90°</option>
            <option value={180}>180°</option>
            <option value={270}>270°</option>
          </select>
        </label>
      )}

      {mode === 'flip' && (
        <label className="flex flex-col gap-1 text-sm w-40">
          <span className="text-muted-foreground">{t('gif_flip')}</span>
          <select value={flipDir} onChange={(e) => setFlipDir(e.target.value as 'horizontal' | 'vertical')} className={`${inputCls} cursor-pointer`}>
            <option value="horizontal">{t('gif_flip_h')}</option>
            <option value="vertical">{t('gif_flip_v')}</option>
          </select>
        </label>
      )}

      {mode === 'watermark' && (
        <div className="flex items-center gap-4 flex-wrap">
          <label className="flex flex-col gap-1 text-sm flex-1 min-w-[160px]">
            <span className="text-muted-foreground">{t('content')}</span>
            <input value={wmText} onChange={(e) => setWmText(e.target.value)} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1 text-sm w-24">
            <span className="text-muted-foreground">{t('opacity')}</span>
            <input type="number" value={wmOpacity} min={1} max={100} onChange={(e) => setWmOpacity(Number(e.target.value))} className={inputCls} />
          </label>
          <label className="flex flex-col gap-1 text-sm w-36">
            <span className="text-muted-foreground">{t('position')}</span>
            <select value={wmPosition} onChange={(e) => setWmPosition(e.target.value)} className={`${inputCls} cursor-pointer`}>
              <option value="top-left">{t('top_left')}</option>
              <option value="top-right">{t('top_right')}</option>
              <option value="center">{t('center')}</option>
              <option value="bottom-left">{t('bottom_left')}</option>
              <option value="bottom-right">{t('bottom_right')}</option>
            </select>
          </label>
        </div>
      )}

      {mode === 'compose' && (
        <div className="flex items-center gap-4 flex-wrap">
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted-foreground">{t('gif_frame_delay')}</span>
            <input type="number" value={composeDuration} min={10} onChange={(e) => setComposeDuration(Number(e.target.value))} className={`w-24 ${inputCls}`} />
          </label>
          <label className="flex flex-col gap-1 text-sm flex-1 min-w-[200px]">
            <span className="text-muted-foreground">{t('gif_output')}</span>
            <input value={outputName} onChange={(e) => setOutputName(e.target.value)} placeholder={`${folder}\\animation.gif`} className={inputCls} />
          </label>
        </div>
      )}

      {mode === 'merge' && (
        <label className="flex flex-col gap-1 text-sm max-w-md">
          <span className="text-muted-foreground">{t('gif_output')}</span>
          <input value={outputName} onChange={(e) => setOutputName(e.target.value)} placeholder={`${folder}\\merged.gif`} className={inputCls} />
        </label>
      )}

      {mode !== 'compose' && mode !== 'merge' && (
        <OutputOptions
          replace={replace}
          doBackup={doBackup}
          out={out}
          onChange={(k, v) => {
            if (k === 'replace') setReplace(v as boolean);
            if (k === 'do_backup') setDoBackup(v as boolean);
            if (k === 'out') setOut(v as string);
          }}
        />
      )}

      <div className="flex items-center gap-3">
        <button type="button" onClick={handleStart} className="btn-cta w-fit">
          <Play size={16} />
          {t('start_gif_edit')}
        </button>
        <span className="text-xs text-[color:var(--color-muted-fg)]">
          {mode === 'compose'
            ? t('gif_selected_count', { n: filteredFiles.length })
            : t('gif_gif_count', { n: gifFiles.length })}
        </span>
      </div>
    </div>
  );
}
