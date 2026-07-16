import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { QuickActionPage } from './pages/QuickActionPage';
import './i18n';
import './styles/globals.css';

async function boot() {
  let label = 'main';
  try {
    const { invoke } = await import('@tauri-apps/api/core');
    label = await invoke<string>('get_window_label');
  } catch {
    try {
      const { getCurrentWindow } = await import('@tauri-apps/api/window');
      label = getCurrentWindow().label;
    } catch {
      label = 'main';
    }
  }

  const root = ReactDOM.createRoot(document.getElementById('root')!);
  root.render(
    <React.StrictMode>{label === 'quick' ? <QuickActionPage /> : <App />}</React.StrictMode>,
  );
}

void boot();
