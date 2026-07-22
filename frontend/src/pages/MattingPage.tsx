import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Scissors, Sparkles, Check } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { OutputOptions } from '../components/OutputOptions';
import { ToolPanel } from '../components/ToolPanel';

const COLOR_PRESETS = [
  { name: 'matting_color_white', hex: '#FFFFFF' },
  { name: 'matting_color_red', hex: '#DC2626' },
  { name: 'matting_color_blue', hex: '#2563EB' },
  { name: 'matting_color_black', hex: '#000000' },
];

function requireOut(replace: boolean, out: string): boolean {
  if (!replace && !out.trim()) {
    alert('Please set an output folder when not replacing originals');
    return false;
  }
  return true;
}

export function MattingPage() {
  const { t } = useTranslation();
  const { startTask } = useAppStore();

  const [engine, setEngine] = useState<'smart' | 'rembg'>('smart');
  const [bgMode, setBgMode] = useState<'transparent' | 'color' | 'mask'>('transparent');
  const [bgColor, setBgColor] = useState('#FFFFFF');
  const [sensitivity, setSensitivity] = useState(30);
  const [feather, setFeather] = useState(1);

  const [replace, setReplace] = useState(false);
  const [doBackup, setDoBackup] = useState(true);
  const [out, setOut] = useState('');

  const handleStart = () => {
    if (!requireOut(replace, out)) return;
    void startTask('matting', {
      engine,
      bg_mode: bgMode,
      bg_color: bgColor,
      sensitivity,
      feather,
      do_backup: doBackup,
      replace,
      out: replace ? null : out,
    });
  };

  return (
    <ToolPanel>
      {/* 引擎选择 / Engine Selection */}
      <div className="flex flex-col gap-1.5 text-xs">
        <span className="font-medium text-foreground">{t('matting_engine')}</span>
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => setEngine('smart')}
            className={`flex items-center justify-center gap-1.5 px-3 py-2 rounded-md border text-xs transition-all cursor-pointer ${
              engine === 'smart'
                ? 'border-primary bg-primary/10 text-primary font-medium'
                : 'border-border bg-background text-muted-foreground hover:bg-muted'
            }`}
          >
            <Sparkles size={14} />
            {t('matting_engine_smart')}
          </button>
          <button
            type="button"
            onClick={() => setEngine('rembg')}
            className={`flex items-center justify-center gap-1.5 px-3 py-2 rounded-md border text-xs transition-all cursor-pointer ${
              engine === 'rembg'
                ? 'border-primary bg-primary/10 text-primary font-medium'
                : 'border-border bg-background text-muted-foreground hover:bg-muted'
            }`}
          >
            <Scissors size={14} />
            {t('matting_engine_rembg')}
          </button>
        </div>

        {engine === 'rembg' && (
          <p className="mt-1 text-[11px] text-muted-foreground bg-primary/5 p-2 rounded border border-primary/20">
            {t('matting_rembg_hint')}
          </p>
        )}
      </div>

      {/* 背景输出模式 / Background Mode */}
      <div className="flex flex-col gap-1.5 text-xs">
        <span className="font-medium text-foreground">{t('matting_bg_mode')}</span>
        <div className="grid grid-cols-3 gap-1.5">
          {(['transparent', 'color', 'mask'] as const).map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => setBgMode(mode)}
              className={`py-1.5 px-2 rounded border text-xs text-center transition-all cursor-pointer ${
                bgMode === mode
                  ? 'border-primary bg-primary/10 text-primary font-medium'
                  : 'border-border bg-background text-muted-foreground hover:bg-muted'
              }`}
            >
              {t(`matting_bg_${mode}`)}
            </button>
          ))}
        </div>
      </div>

      {/* 背景颜色选择 (当模式为 color 时显示) */}
      {bgMode === 'color' && (
        <div className="flex flex-col gap-2 p-2.5 rounded-lg border border-border/80 bg-background/50 text-xs">
          <span className="font-medium text-foreground">{t('matting_color_select')}</span>
          <div className="flex items-center gap-2">
            {COLOR_PRESETS.map((preset) => (
              <button
                key={preset.hex}
                type="button"
                onClick={() => setBgColor(preset.hex)}
                className={`w-7 h-7 rounded-full border border-border flex items-center justify-center transition-transform cursor-pointer ${
                  bgColor.toUpperCase() === preset.hex.toUpperCase()
                    ? 'ring-2 ring-primary ring-offset-1 scale-110'
                    : 'hover:scale-105'
                }`}
                style={{ backgroundColor: preset.hex }}
                title={t(preset.name)}
              >
                {bgColor.toUpperCase() === preset.hex.toUpperCase() && (
                  <Check
                    size={13}
                    className={preset.hex === '#FFFFFF' ? 'text-black' : 'text-white'}
                  />
                )}
              </button>
            ))}

            <label className="flex items-center gap-1.5 ml-auto cursor-pointer">
              <span className="text-[11px] text-muted-foreground">{t('matting_color_custom')}</span>
              <input
                type="color"
                value={bgColor}
                onChange={(e) => setBgColor(e.target.value)}
                className="w-7 h-7 p-0 border border-border rounded cursor-pointer bg-transparent"
              />
            </label>
          </div>
        </div>
      )}

      {/* 敏感度 / Sensitivity Slider */}
      <label className="flex flex-col gap-1 text-xs">
        <div className="flex justify-between">
          <span className="text-muted-foreground">{t('matting_sensitivity')}</span>
          <span className="font-mono text-foreground">{sensitivity}</span>
        </div>
        <input
          type="range"
          min="1"
          max="100"
          value={sensitivity}
          onChange={(e) => setSensitivity(Number(e.target.value))}
          className="w-full h-1.5 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
        />
      </label>

      {/* 边缘羽化 / Feather Slider */}
      <label className="flex flex-col gap-1 text-xs">
        <div className="flex justify-between">
          <span className="text-muted-foreground">{t('matting_feather')}</span>
          <span className="font-mono text-foreground">{feather} px</span>
        </div>
        <input
          type="range"
          min="0"
          max="10"
          value={feather}
          onChange={(e) => setFeather(Number(e.target.value))}
          className="w-full h-1.5 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
        />
      </label>

      {/* 输出选项 */}
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

      <button onClick={handleStart} className="btn-cta w-fit mt-1">
        <Scissors size={16} />
        {t('start_matting')}
      </button>
    </ToolPanel>
  );
}
