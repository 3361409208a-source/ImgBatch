import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { X, Package, Sliders, Archive, Key, Languages, Check } from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { ExtensionPackPanel } from './ExtensionPackPanel';
import { BackupManager } from './BackupManager';
import { api } from '../api/client';

interface SettingsModalProps {
  open: boolean;
  onClose: () => void;
  initialTab?: 'extensions' | 'general' | 'backups';
}

export function SettingsModal({ open, onClose, initialTab = 'extensions' }: SettingsModalProps) {
  const { t } = useTranslation();
  const { language, setLanguage, loadConfig } = useAppStore();
  const [activeTab, setActiveTab] = useState<'extensions' | 'general' | 'backups'>(initialTab);

  const [apiKey, setApiKey] = useState('');
  const [savedKey, setSavedKey] = useState(false);

  useEffect(() => {
    if (open) {
      setActiveTab(initialTab);
      void api.getConfig().then((cfg) => {
        if (cfg.deepseek_api_key && typeof cfg.deepseek_api_key === 'string') {
          setApiKey(cfg.deepseek_api_key);
        }
      });
    }
  }, [open, initialTab]);

  if (!open) return null;

  const handleSaveApiKey = async () => {
    try {
      await api.saveConfig({ deepseek_api_key: apiKey });
      await loadConfig();
      setSavedKey(true);
      setTimeout(() => setSavedKey(false), 2000);
    } catch (e) {
      alert(String(e));
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-2xl bg-surface border border-border rounded-xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-border bg-surface shrink-0">
          <div className="flex items-center gap-2">
            <Sliders size={18} className="text-primary" />
            <h2 className="text-sm font-semibold text-foreground">{t('settings_center')}</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors cursor-pointer"
          >
            <X size={16} />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-border bg-muted/30 px-5 gap-1 shrink-0">
          <button
            type="button"
            onClick={() => setActiveTab('extensions')}
            className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-medium border-b-2 transition-all cursor-pointer ${
              activeTab === 'extensions'
                ? 'border-primary text-primary bg-background/50 font-semibold'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Package size={14} />
            {t('settings_tab_extensions')}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('general')}
            className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-medium border-b-2 transition-all cursor-pointer ${
              activeTab === 'general'
                ? 'border-primary text-primary bg-background/50 font-semibold'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Sliders size={14} />
            {t('settings_tab_general')}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('backups')}
            className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-medium border-b-2 transition-all cursor-pointer ${
              activeTab === 'backups'
                ? 'border-primary text-primary bg-background/50 font-semibold'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Archive size={14} />
            {t('settings_tab_backups')}
          </button>
        </div>

        {/* Tab Content Body */}
        <div className="flex-1 overflow-y-auto p-5 min-h-0 space-y-4">
          {activeTab === 'extensions' && (
            <div>
              <ExtensionPackPanel />
            </div>
          )}

          {activeTab === 'general' && (
            <div className="space-y-4">
              {/* Language Setting */}
              <div className="p-4 rounded-lg border border-border bg-background/50 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Languages size={16} className="text-primary" />
                    <span className="text-xs font-medium text-foreground">{t('language_setting')}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => setLanguage('zh')}
                      className={`px-3 py-1 text-xs rounded border transition-colors cursor-pointer ${
                        language === 'zh'
                          ? 'border-primary bg-primary/10 text-primary font-medium'
                          : 'border-border bg-background text-muted-foreground'
                      }`}
                    >
                      简体中文
                    </button>
                    <button
                      type="button"
                      onClick={() => setLanguage('en')}
                      className={`px-3 py-1 text-xs rounded border transition-colors cursor-pointer ${
                        language === 'en'
                          ? 'border-primary bg-primary/10 text-primary font-medium'
                          : 'border-border bg-background text-muted-foreground'
                      }`}
                    >
                      English
                    </button>
                  </div>
                </div>
              </div>

              {/* AI Key Setting */}
              <div className="p-4 rounded-lg border border-border bg-background/50 space-y-2.5">
                <div className="flex items-center gap-2">
                  <Key size={16} className="text-primary" />
                  <span className="text-xs font-medium text-foreground">{t('ai_key_setting')}</span>
                </div>
                <p className="text-[11px] text-muted-foreground">
                  {t('ai_key_hint')}
                </p>
                <div className="flex gap-2">
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="sk-..."
                    className="flex-1 px-3 py-1.5 border border-border rounded-md bg-background text-xs font-mono outline-none focus:border-primary"
                  />
                  <button
                    type="button"
                    onClick={() => void handleSaveApiKey()}
                    className="btn-primary h-8 text-xs px-3"
                  >
                    {savedKey ? <Check size={14} /> : null}
                    {savedKey ? t('saved') : t('save')}
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'backups' && (
            <div className="space-y-3">
              <BackupManager open={true} inline />
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex justify-end px-5 py-3 border-t border-border bg-surface shrink-0">
          <button type="button" onClick={onClose} className="btn-outline text-xs px-4">
            {t('close')}
          </button>
        </div>
      </div>
    </div>
  );
}
