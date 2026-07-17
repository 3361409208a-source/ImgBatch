import { CONTEXT_MENU_ITEMS, DESKTOP_HIGHLIGHTS } from '../content';
import { FeatureIcon } from './icons';

export function DesktopHighlights() {
  return (
    <section id="desktop" className="scroll-mt-24 bg-secondary/[0.03] py-16 sm:py-24">
      <div className="section-container">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-primary">Desktop</p>
            <h2 className="section-title mt-2">为 Windows 工作流而生</h2>
            <p className="section-subtitle">
              不只是打开一个窗口——ImgBatch 深度集成资源管理器，让你在最熟悉的地方完成批处理。
            </p>

            <ul className="mt-10 space-y-5">
              {DESKTOP_HIGHLIGHTS.map((item) => (
                <li key={item.title} className="flex gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary text-on-primary shadow-sm">
                    <FeatureIcon name={item.icon} className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground">{item.title}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-muted-fg">{item.desc}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <div className="relative">
            <div className="rounded-2xl border border-border bg-surface p-6 shadow-lg">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted-fg">Context Menu</p>
              <div className="mt-4 space-y-2 font-mono text-sm">
                <div className="rounded-lg bg-muted px-4 py-3 text-muted-fg">打开(O)</div>
                <div className="rounded-lg bg-muted px-4 py-3 text-muted-fg">发送到(N)</div>
                {CONTEXT_MENU_ITEMS.map((label) => (
                  <div
                    key={label}
                    className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-2.5 font-medium text-primary"
                  >
                    ImgBatch {label} ▸
                  </div>
                ))}
              </div>
            </div>

            <div className="absolute -right-2 -top-3 rounded-full bg-accent px-3 py-1 text-xs font-bold text-on-primary shadow-md sm:-right-4">
              右键即用
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
