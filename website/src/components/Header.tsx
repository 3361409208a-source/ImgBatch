import { useEffect, useState } from 'react';
import { Github, Menu, X } from './icons';
import { NAV, SITE } from '../content';

export function Header() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        scrolled ? 'border-b border-border/80 bg-surface/90 shadow-sm backdrop-blur-md' : 'bg-transparent'
      }`}
    >
      <div className="section-container flex h-16 items-center justify-between">
        <a href="#" className="flex items-center gap-2.5 font-bold text-foreground">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-sm text-on-primary shadow-md">
            IB
          </span>
          <span className="text-lg tracking-tight">{SITE.name}</span>
        </a>

        <nav className="hidden items-center gap-8 md:flex">
          {NAV.map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              className="text-sm font-medium text-muted-fg transition-colors hover:text-foreground"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <a
            href={SITE.github}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-muted-fg transition-colors hover:bg-muted hover:text-foreground"
          >
            <Github className="h-4 w-4" />
            GitHub
          </a>
          <a href="#download" className="btn-primary">
            免费下载
          </a>
        </div>

        <button
          type="button"
          className="inline-flex rounded-lg p-2 text-foreground md:hidden"
          aria-label={open ? '关闭菜单' : '打开菜单'}
          onClick={() => setOpen((v) => !v)}
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {open && (
        <div className="border-t border-border bg-surface px-4 py-4 md:hidden">
          <nav className="flex flex-col gap-1">
            {NAV.map((item) => (
              <a
                key={item.id}
                href={`#${item.id}`}
                className="rounded-lg px-3 py-2.5 text-sm font-medium text-foreground hover:bg-muted"
                onClick={() => setOpen(false)}
              >
                {item.label}
              </a>
            ))}
            <a
              href={SITE.github}
              target="_blank"
              rel="noreferrer"
              className="rounded-lg px-3 py-2.5 text-sm font-medium text-muted-fg hover:bg-muted"
            >
              GitHub
            </a>
            <a href="#download" className="btn-primary mt-2" onClick={() => setOpen(false)}>
              免费下载
            </a>
          </nav>
        </div>
      )}
    </header>
  );
}
