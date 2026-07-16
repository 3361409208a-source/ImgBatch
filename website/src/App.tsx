import { Header } from './components/Header';
import { Hero } from './components/Hero';
import { Features } from './components/Features';
import { DesktopHighlights } from './components/DesktopHighlights';
import { HowItWorks } from './components/HowItWorks';
import { DownloadSection } from './components/DownloadSection';
import { Footer } from './components/Footer';

export default function App() {
  return (
    <div className="min-h-screen">
      <Header />
      <main>
        <Hero />
        <Features />
        <DesktopHighlights />
        <HowItWorks />
        <DownloadSection />
      </main>
      <Footer />
    </div>
  );
}
