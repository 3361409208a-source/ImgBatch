import React from 'react';
import ReactDOM from 'react-dom/client';
import { QuickActionPage } from './pages/QuickActionPage';
import './i18n';
import './styles/globals.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QuickActionPage />
  </React.StrictMode>,
);
