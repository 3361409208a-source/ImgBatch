import { Download, Github } from './icons';
import { SITE } from '../content';

export function DownloadSection() {
  return (
    <section id="download" className="scroll-mt-24 py-16 sm:py-24">
      <div className="section-container">
        <div className="relative overflow-hidden rounded-3xl border border-primary/20 bg-gradient-to-br from-primary to-accent px-6 py-12 text-on-primary shadow-xl sm:px-10 sm:py-14">
          <div className="pointer-events-none absolute -right-10 -top-10 h-48 w-48 rounded-full bg-white/10 blur-2xl" />
          <div className="pointer-events-none absolute -bottom-16 -left-10 h-56 w-56 rounded-full bg-black/10 blur-2xl" />

          <div className="relative mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-extrabold tracking-tight sm:text-4xl">立即下载 ImgBatch</h2>
            <p className="mt-4 text-base leading-relaxed text-on-primary/90 sm:text-lg">
              当前版本 v{SITE.version}，支持 Windows 10/11。安装包包含桌面应用、API 侧车与资源管理器右键菜单。
            </p>

            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <a
                href={SITE.releases}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-lg bg-surface px-6 py-3 text-sm font-bold text-primary shadow-md transition-transform hover:scale-[1.02]"
              >
                <Download className="h-4 w-4" />
                下载最新安装包
              </a>
              <a
                href={SITE.github}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-lg border border-on-primary/30 bg-white/10 px-6 py-3 text-sm font-semibold text-on-primary backdrop-blur transition-colors hover:bg-white/20"
              >
                <Github className="h-4 w-4" />
                查看源码
              </a>
            </div>

            <p className="mt-6 text-xs text-on-primary/75">
              部署到 Vercel 后，可将上方链接替换为 GitHub Releases 或自有 CDN 地址。
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
