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
    {
      id: 'ffmpeg',
      name: 'FFmpeg 音视频扩展包',
      name_en: 'FFmpeg Media Pack',
      description: '解锁视频转 GIF/WebP、WebM 透明压缩等音视频处理能力。',
      description_en: 'Unlock video→GIF/WebP and WebM alpha compression.',
      download_url: 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
      install_dir: '%USERPROFILE%\\.imgbatch\\extensions\\ffmpeg',
      size_hint: '~80 MB 下载 · 解压至用户目录',
      size_hint_en: '~80 MB download · extracts to user folder',
      installed: false,
      install_path: null,
      unlocks: [
        '视频 → 动画 WebP / GIF',
        'WebM 透明通道压缩',
        'VP9 Alpha 正确解码',
      ],
      unlocks_en: [
        'Video → animated WebP / GIF',
        'WebM alpha compression',
        'Correct VP9 alpha decode',
      ],
    },
  ],
  locked_count: 2,
  unlocked_count: 0,
  total_count: 2,
};
