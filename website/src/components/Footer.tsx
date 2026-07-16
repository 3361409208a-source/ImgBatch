import { Github } from './icons';
import { SITE } from '../content';

export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-border py-10">
      <div className="section-container flex flex-col items-center justify-between gap-6 sm:flex-row">
        <div className="text-center sm:text-left">
          <p className="font-bold text-foreground">{SITE.name}</p>
          <p className="mt-1 text-sm text-muted-fg">
            {SITE.tagline} · {SITE.license} License
          </p>
        </div>

        <div className="flex items-center gap-6 text-sm">
          <a
            href={SITE.github}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 font-medium text-muted-fg transition-colors hover:text-foreground"
          >
            <Github className="h-4 w-4" />
            GitHub
          </a>
          <a href="#features" className="font-medium text-muted-fg transition-colors hover:text-foreground">
            功能
          </a>
          <a href="#download" className="font-medium text-muted-fg transition-colors hover:text-foreground">
            下载
          </a>
        </div>
      </div>
      <p className="section-container mt-6 text-center text-xs text-muted-fg sm:text-left">
        © {year} {SITE.name}. All rights reserved.
      </p>
    </footer>
  );
}
