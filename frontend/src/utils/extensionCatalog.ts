import type { ExtensionCatalogResponse } from '../api/types';

export const FALLBACK_EXTENSION_CATALOG: ExtensionCatalogResponse = {
  extensions: [
    {
      id: 'libreoffice',
      name: 'Office 文档扩展包',
      name_en: 'Office Document Pack',
      description: '解锁 Word / Excel / PPT 与 PDF 互转、Office 格式批量转换。',
      description_en: 'Unlock Word/Excel/PPT ↔ PDF and batch Office conversions.',
      download_url:
        'https://download.documentfoundation.org/libreoffice/portable/25.8.5/LibreOfficePortablePrevious_25.8.5_MultilingualStandard.paf.exe',
      install_dir: '%USERPROFILE%\\.imgbatch\\extensions\\libreoffice',
      size_hint: '~200 MB 下载 · 解压至用户目录',
      size_hint_en: '~200 MB download · extracts to user folder',
      installed: false,
      install_path: null,
      unlocks: [
        '办公文档 → PDF',
        'PDF → Word (DOCX)',
        'Word / Excel / PPT 格式互转',
        'RTF / ODF / HTML 文档转换',
      ],
      unlocks_en: [
        'Office → PDF',
        'PDF → Word (DOCX)',
        'Word / Excel / PPT cross-convert',
        'RTF / ODF / HTML document convert',
      ],
    },
  ],
  locked_count: 1,
  unlocked_count: 0,
  total_count: 1,
};
