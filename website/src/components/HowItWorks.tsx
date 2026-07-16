import { STEPS } from '../content';

export function HowItWorks() {
  return (
    <section id="how" className="scroll-mt-24 py-16 sm:py-24">
      <div className="section-container">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-primary">Workflow</p>
          <h2 className="section-title mt-2">三步开始批处理</h2>
          <p className="section-subtitle mx-auto">
            无论你是从主窗口精细操作，还是通过右键快速处理，流程都足够简单。
          </p>
        </div>

        <ol className="mt-14 grid gap-6 md:grid-cols-3">
          {STEPS.map((step, index) => (
            <li key={step.step} className="relative card text-left">
              {index < STEPS.length - 1 && (
                <span
                  className="pointer-events-none absolute -right-3 top-1/2 hidden h-px w-6 bg-border md:block"
                  aria-hidden
                />
              )}
              <span className="font-mono text-sm font-bold text-primary">{step.step}</span>
              <h3 className="mt-3 text-xl font-bold text-foreground">{step.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-muted-fg">{step.desc}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
