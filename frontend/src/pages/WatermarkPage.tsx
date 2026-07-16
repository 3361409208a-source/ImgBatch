import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Play, FolderOpen } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { OutputOptions } from '../components/OutputOptions';

const POSITIONS = ['top-left', 'top-right', 'center', 'bottom-left', 'bottom-right'];

function requireOut(replace: boolean, out: string): boolean {
  if (!replace && !out.trim()) {
    alert('Please set an output folder when not replacing originals');
    return false;
  }
  return true;
}

export function WatermarkPage() {
  const { t } = useTranslation();
  const { startTask } = useAppStore();
  const [wmType, setWmType] = useState('text');
  const [text, setText] = useState('水印');
  const [fontsize, setFontsize] = useState(36);
  const [opacity, setOpacity] = useState(50);
  const [position, setPosition] = useState('bottom-right');
  const [color, setColor] = useState('#ffffff');
  const [imagePath, setImagePath] = useState('');
  const [imgScale, setImgScale] = useState(0.2);
  const [replace, setReplace] = useState(true);
  const [doBackup, setDoBackup] = useState(true);
  const [out, setOut] = useState('');

  const pickImage = async () => {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const files = await invoke<string[]>('pick_files');
      if (files?.[0]) setImagePath(files[0]);
    } catch {
      const path = prompt('Watermark image path:');
      if (path) setImagePath(path);
    }
  };

  const handleStart = () => {
    if (!requireOut(replace, out)) return;
    if (wmType === 'image' && !imagePath.trim()) {
      alert('Please select a watermark image');
      return;
    }
    void startTask('watermark', {
      params: {
        type: wmType,
        text,
        fontsize,
        opacity: opacity / 100,
        position,
        color,
        image_path: imagePath,
        img_scale: imgScale,
      },
      do_backup: doBackup,
      replace,
      out: replace ? null : out,
    });
  };

  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="flex items-center gap-4 flex-wrap">
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="radio" checked={wmType === 'text'} onChange={() => setWmType('text')} className="accent-primary cursor-pointer" />
          {t('text_type')}
        </label>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="radio" checked={wmType === 'image'} onChange={() => setWmType('image')} className="accent-primary cursor-pointer" />
          {t('image_type')}
        </label>
      </div>
      {wmType === 'text' ? (
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted-foreground">{t('content')}</span>
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none"
          />
        </label>
      ) : (
        <div className="flex flex-col gap-2 text-sm">
          <span className="text-muted-foreground">{t('image_type')}</span>
          <div className="flex gap-2">
            <input
              type="text"
              value={imagePath}
              onChange={(e) => setImagePath(e.target.value)}
              placeholder="C:\watermark.png"
              className="flex-1 px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none"
            />
            <button
              type="button"
              onClick={() => void pickImage()}
              className="flex items-center gap-1 px-3 py-1.5 border border-border rounded hover:bg-muted cursor-pointer"
            >
              <FolderOpen size={14} />
              {t('browse')}
            </button>
          </div>
          <label className="flex flex-col gap-1 w-40">
            <span className="text-muted-foreground">Scale</span>
            <input
              type="number"
              min={0.05}
              max={1}
              step={0.05}
              value={imgScale}
              onChange={(e) => setImgScale(Number(e.target.value))}
              className="px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none"
            />
          </label>
        </div>
      )}
      <div className="flex items-center gap-6 flex-wrap">
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted-foreground">{t('font_size')}</span>
          <input
            type="number"
            value={fontsize}
            onChange={(e) => setFontsize(Number(e.target.value))}
            className="w-20 px-2 py-1.5 border border-border rounded bg-background focus:border-primary outline-none"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted-foreground">{t('opacity')} %</span>
          <div className="flex items-center gap-2">
            <input type="range" min="0" max="100" value={opacity} onChange={(e) => setOpacity(Number(e.target.value))} />
            <span className="font-mono text-xs w-8">{opacity}%</span>
          </div>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted-foreground">{t('position')}</span>
          <select
            value={position}
            onChange={(e) => setPosition(e.target.value)}
            className="px-2 py-1.5 border border-border rounded bg-background cursor-pointer focus:border-primary outline-none"
          >
            {POSITIONS.map((p) => (
              <option key={p} value={p}>
                {t(p)}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted-foreground">{t('color')}</span>
          <input
            type="color"
            value={color}
            onChange={(e) => setColor(e.target.value)}
            className="w-12 h-8 border border-border rounded cursor-pointer"
          />
        </label>
      </div>
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
      <button
        onClick={handleStart}
        className="btn-cta w-fit"
      >
        <Play size={16} />
        {t('start_watermark')}
      </button>
    </div>
  );
}
