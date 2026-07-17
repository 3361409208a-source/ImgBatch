import { ArrowRight, Download } from './icons';
import { SITE, STATS } from '../content';

export function Hero() {
  return (
    <section className="relative overflow-hidden pt-28 pb-16 sm:pt-32 sm:pb-24">
      <div className="pointer-events-none absolute -right-24 top-10 h-72 w-72 rounded-full bg-primary/10 blur-3xl" />
      <div className="pointer-events-none absolute -left-16 bottom-0 h-64 w-64 rounded-full bg-secondary/5 blur-3xl" />

      <div className="section-container">
        <div className="grid items-center gap-12 lg:grid-cols-[1.1fr_0.9fr] lg:gap-16">
          <div className="animate-fade-up">
            <span className="badge">v{SITE.version} · Windows 桌面版</span>
            <h1 className="mt-5 text-4xl font-extrabold leading-[1.1] tracking-tight text-foreground sm:text-5xl lg:text-6xl">
              {SITE.tagline}
            </h1>
            <p className="mt-2 text-lg font-medium text-primary sm:text-xl">{SITE.taglineEn}</p>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-muted-fg sm:text-lg">
              压缩、转换、重命名、水印、AI 重命名、裁剪透明、检查、规范化、精灵图与 GIF 编辑——
              面向设计师与开发者的本地批处理工具，支持资源管理器独立右键菜单与快捷弹窗。
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <a href="#download" className="btn-primary">
                <Download className="h-4 w-4" />
                下载 Windows 版
              </a>
              <a href="#features" className="btn-outline">
                查看功能
                <ArrowRight className="h-4 w-4" />
              </a>
            </div>

            <dl className="mt-10 grid grid-cols-3 gap-4 border-t border-border pt-8 sm:gap-8">
              {STATS.map((item) => (
                <div key={item.label}>
                  <dt className="text-2xl font-bold text-primary sm:text-3xl">{item.value}</dt>
                  <dd className="mt-1 text-xs font-medium text-muted-fg sm:text-sm">{item.label}</dd>
                </div>
              ))}
            </dl>
          </div>

          <div className="relative animate-fade-up [animation-delay:120ms]">
            <div className="absolute -inset-4 rounded-[2rem] bg-gradient-to-br from-primary/20 via-transparent to-secondary/10 blur-2xl" />
            <div className="relative overflow-hidden rounded-2xl border border-border bg-surface shadow-xl">
              <div className="flex items-center gap-2 border-b border-border bg-muted/60 px-4 py-3">
                <span className="h-3 w-3 rounded-full bg-red-400/80" />
                <span className="h-3 w-3 rounded-full bg-amber-400/80" />
                <span className="h-3 w-3 rounded-full bg-emerald-400/80" />
                <span className="ml-2 text-xs font-medium text-muted-fg">ImgBatch — 批处理工作台</span>
              </div>
              <div className="grid gap-4 p-5 sm:p-6">
                <MockPanel title="压缩 Compress" progress={72} detail="预估节省 38% · 保留 EXIF" />
                <MockPanel title="批量重命名 Rename" progress={100} detail="photo_001 → cover_001 · 无冲突" />
                <MockPanel title="图片检查 Inspect" progress={45} detail="分析 PNG 画布与内容边距" />
              </div>
            </div>
            <div className="absolute -bottom-4 -left-4 hidden rounded-xl border border-border bg-surface px-4 py-3 shadow-lg sm:block">
              <p className="text-xs font-semibold text-foreground">右键快捷操作</p>
              <p className="mt-0.5 text-xs text-muted-fg">压缩 · 转换 · 重命名 · 水印 · GIF…</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function MockPanel({
  title,
  progress,
  detail,
}: {
  title: string;
  progress: number;
  detail: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-background/80 p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold text-foreground">{title}</p>
        <span className="font-mono text-xs text-primary">{progress}%</span>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-gradient-to-r from-primary to-accent transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="mt-2 text-xs text-muted-fg">{detail}</p>
    </div>
  );
}
