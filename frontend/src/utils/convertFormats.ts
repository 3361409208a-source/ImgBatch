export interface ConvertTarget {
  ext: string;
  label: string;
  group: 'common' | 'other';
  supports_quality: boolean;
}

export interface ConvertPreset {
  id: string;
  label: string;
  target_fmt: string;
  quality: number | null;
  hint: string;
}

export interface ConvertCatalog {
  targets: ConvertTarget[];
  presets: ConvertPreset[];
  features: {
    heic_input: boolean;
    avif_output: boolean;
  };
}

export const FALLBACK_CONVERT_CATALOG: ConvertCatalog = {
  targets: [
    { ext: '.jpg', label: 'JPG', group: 'common', supports_quality: true },
    { ext: '.png', label: 'PNG', group: 'common', supports_quality: false },
    { ext: '.webp', label: 'WEBP', group: 'common', supports_quality: true },
    { ext: '.jpeg', label: 'JPEG', group: 'other', supports_quality: true },
    { ext: '.bmp', label: 'BMP', group: 'other', supports_quality: false },
    { ext: '.tiff', label: 'TIFF', group: 'other', supports_quality: false },
    { ext: '.gif', label: 'GIF', group: 'other', supports_quality: false },
    { ext: '.ico', label: 'ICO', group: 'other', supports_quality: false },
  ],
  presets: [
    { id: 'web_jpg', label: '网页 JPG', target_fmt: '.jpg', quality: 85, hint: '通用网页与分享' },
    { id: 'web_webp', label: 'WebP 体积小', target_fmt: '.webp', quality: 82, hint: '现代浏览器，更小体积' },
    { id: 'png_transparent', label: 'PNG 透明', target_fmt: '.png', quality: null, hint: '保留透明通道' },
    { id: 'print_tiff', label: 'TIFF 打印', target_fmt: '.tiff', quality: null, hint: '印刷与归档' },
    { id: 'icon_ico', label: '图标 ICO', target_fmt: '.ico', quality: null, hint: 'Windows 图标' },
  ],
  features: { heic_input: false, avif_output: false },
};

export const IMAGE_INPUT_EXT = new Set([
  '.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tif', '.tiff', '.ico', '.heic', '.heif', '.avif',
]);

export function targetSupportsQuality(
  catalog: ConvertCatalog,
  targetFmt: string,
): boolean {
  return catalog.targets.some((t) => t.ext === targetFmt && t.supports_quality);
}

export function groupTargets(catalog: ConvertCatalog) {
  const common = catalog.targets.filter((t) => t.group === 'common');
  const other = catalog.targets.filter((t) => t.group === 'other');
  return { common, other };
}
