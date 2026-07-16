import { FEATURES } from '../content';
import { FeatureIcon } from './icons';

export function Features() {
  return (
    <section id="features" className="scroll-mt-24 py-16 sm:py-24">
      <div className="section-container">
        <div className="max-w-3xl">
          <p className="text-sm font-semibold uppercase tracking-wider text-primary">Features</p>
          <h2 className="section-title mt-2">八大核心功能</h2>
          <p className="section-subtitle">
            从日常压缩到 AI 重命名，覆盖图片批处理常见场景。所有处理在本地完成，图片不会上传到云端。
          </p>
        </div>

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((feature) => (
            <article key={feature.title} className="card group">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-on-primary">
                <FeatureIcon name={feature.icon} className="h-5 w-5" />
              </div>
              <h3 className="mt-4 text-lg font-bold text-foreground">{feature.title}</h3>
              <p className="text-xs font-medium text-primary">{feature.titleEn}</p>
              <p className="mt-3 text-sm leading-relaxed text-muted-fg">{feature.desc}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
