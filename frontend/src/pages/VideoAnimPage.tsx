import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Play } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { OutputOptions } from '../components/OutputOptions';
import { ToolPanel } from '../components/ToolPanel';
import { FfmpegInstallBar } from '../components/FfmpegInstallBar';

const VIDEO_RE = /\.(webm|mp4|mov|avi|mkv|m4v)$/i;

function requireOut(replace: boolean, out: string): boolean {
  if (!replace && !out.trim()) {
    alert('Please set an output folder when not replacing originals');
    return false;
  }
  return true;
}

export function VideoAnimPage() {
  const { t } = useTranslation();
  const { startTask, filteredFiles } = useAppStore();
  const [target, setTarget] = useState<'webp' | 'gif'>('webp');
  const [maxEdge, setMaxEdge] = useState(0);
  const [fps, setFps] = useState(24);
  const [quality, setQuality] = useState(80);
  const [colors, setColors] = useState(256);
  const [keepAlpha, setKeepAlpha] = useState(true);
  const [cleanFringe, setCleanFringe] = useState(false);
  const [whiteKey, setWhiteKey] = useState(false);
  const [whiteKeySimilarity, setWhiteKeySimilarity] = useState(0.12);
  const [whiteKeyBlend, setWhiteKeyBlend] = useState(0.04);
  const [replace, setReplace] = useState(false);
  const [doBackup, setDoBackup] = useState(true);
  const [out, setOut] = useState('');

  const videoCount = useMemo(
    () => filteredFiles.filter((f) => VIDEO_RE.test(f.name)).length,
    [filteredFiles],
  );

  const handleStart = () => {
    if (!requireOut(replace, out)) return;
    if (videoCount === 0) {
      alert(t('video_anim_no_files'));
      return;
    }
    void startTask('video_anim', {
      target: target === 'gif' ? '.gif' : '.webp',
      max_edge: maxEdge,
      fps,
      quality,
      colors,
      keep_alpha: keepAlpha || whiteKey,
      clean_fringe: cleanFringe,
      white_key: whiteKey,
      white_key_similarity: whiteKeySimilarity,
      white_key_blend: whiteKeyBlend,
      do_backup: doBackup,
      replace,
      out: replace ? null : out,
    });
  };

  return (
    <ToolPanel>
      <p className="text-xs text-muted-foreground max-w-xl">{t('video_anim_hint')}</p>
      <FfmpegInstallBar />

      <div className="flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-1.5 w-36">
          <span className="label-muted">{t('video_anim_target')}</span>
          <select
            value={target}
            onChange={(e) => setTarget(e.target.value as 'webp' | 'gif')}
            className="field cursor-pointer"
          >
            <option value="webp">WebP</option>
            <option value="gif">GIF</option>
          </select>
        </label>

        <label className="flex flex-col gap-1.5 w-28">
          <span className="label-muted">{t('webm_max_edge')}</span>
          <input
            type="number"
            min={0}
            max={4096}
            value={maxEdge}
            onChange={(e) => setMaxEdge(Number(e.target.value))}
            className="field"
            title={t('video_anim_max_edge_hint')}
          />
        </label>

        <label className="flex flex-col gap-1.5 w-24">
          <span className="label-muted">{t('webm_fps')}</span>
          <input
            type="number"
            min={1}
            max={60}
            value={fps}
            onChange={(e) => setFps(Number(e.target.value))}
            className="field"
          />
        </label>

        {target === 'webp' ? (
          <label className="flex flex-col gap-1.5 w-40">
            <span className="label-muted">{t('quality')} {quality}</span>
            <input
              type="range"
              min={1}
              max={100}
              value={quality}
              onChange={(e) => setQuality(Number(e.target.value))}
            />
          </label>
        ) : (
          <label className="flex flex-col gap-1.5 w-28">
            <span className="label-muted">{t('gif_colors')}</span>
            <input
              type="number"
              min={2}
              max={256}
              value={colors}
              onChange={(e) => setColors(Number(e.target.value))}
              className="field"
            />
          </label>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={whiteKey}
            onChange={(e) => {
              const checked = e.target.checked;
              setWhiteKey(checked);
              if (checked) setKeepAlpha(true);
            }}
            className="accent-primary"
          />
          {t('video_anim_white_key')}
        </label>
        {whiteKey && (
          <div className="flex flex-wrap items-end gap-4 pl-6">
            <label className="flex flex-col gap-1.5 w-48">
              <span className="label-muted">
                {t('video_anim_white_key_similarity')} {whiteKeySimilarity.toFixed(2)}
              </span>
              <input
                type="range"
                min={0.05}
                max={0.3}
                step={0.01}
                value={whiteKeySimilarity}
                onChange={(e) => setWhiteKeySimilarity(Number(e.target.value))}
              />
            </label>
            <label className="flex flex-col gap-1.5 w-48">
              <span className="label-muted">
                {t('video_anim_white_key_blend')} {whiteKeyBlend.toFixed(2)}
              </span>
              <input
                type="range"
                min={0.01}
                max={0.1}
                step={0.01}
                value={whiteKeyBlend}
                onChange={(e) => setWhiteKeyBlend(Number(e.target.value))}
              />
            </label>
          </div>
        )}
        <p className="text-xs text-muted-foreground">{t('video_anim_white_key_hint')}</p>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={keepAlpha || whiteKey}
            disabled={whiteKey}
            onChange={(e) => setKeepAlpha(e.target.checked)}
            className="accent-primary"
          />
          {t('webm_keep_alpha')}
        </label>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={cleanFringe}
            onChange={(e) => setCleanFringe(e.target.checked)}
            className="accent-primary"
          />
          {t('video_anim_clean_fringe')}
        </label>
        <p className="text-xs text-muted-foreground">{t('video_anim_clean_fringe_hint')}</p>
      </div>

      <p className="text-[12px] font-mono text-[color:var(--color-muted-fg)]">
        {t('video_anim_file_count', { n: videoCount })}
      </p>

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

      <button type="button" onClick={handleStart} className="btn-cta w-fit">
        <Play size={14} strokeWidth={1.75} />
        {t('start_video_anim')}
      </button>
    </ToolPanel>
  );
}
