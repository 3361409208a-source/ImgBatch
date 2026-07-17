export interface DocTarget {
  ext: string;
  label: string;
  group: 'common' | 'other';
}

export interface DocPreset {
  id: string;
  label: string;
  target_fmt: string;
  hint: string;
}

export interface DocCatalog {
  targets: DocTarget[];
  presets: DocPreset[];
  features: {
    libreoffice: boolean;
    pymupdf: boolean;
  };
  inputs: string[];
}

export type ScanKind = 'image' | 'document' | 'all';

export const FALLBACK_DOC_CATALOG: DocCatalog = {
  targets: [
    { ext: '.pdf', label: 'PDF', group: 'common' },
    { ext: '.docx', label: 'DOCX', group: 'common' },
    { ext: '.xlsx', label: 'XLSX', group: 'common' },
    { ext: '.png', label: 'PNG', group: 'common' },
    { ext: '.jpg', label: 'JPG', group: 'common' },
    { ext: '.txt', label: 'TXT', group: 'other' },
    { ext: '.html', label: 'HTML', group: 'other' },
    { ext: '.csv', label: 'CSV', group: 'other' },
  ],
  presets: [
    { id: 'pdf_png', label: 'PDF→PNG', target_fmt: '.png', hint: 'PDF 每页导出为 PNG' },
    { id: 'pdf_txt', label: 'PDF→TXT', target_fmt: '.txt', hint: '提取 PDF 文本' },
    { id: 'csv_xlsx', label: 'CSV→Excel', target_fmt: '.xlsx', hint: 'CSV 转 XLSX' },
    { id: 'txt_pdf', label: 'TXT→PDF', target_fmt: '.pdf', hint: '文本转 PDF' },
  ],
  features: { libreoffice: false, pymupdf: true },
  inputs: ['.pdf', '.docx', '.xlsx', '.txt', '.csv'],
};

export const DOC_FILTER_FORMATS = [
  'ALL', 'PDF', 'DOC', 'DOCX', 'XLS', 'XLSX', 'PPT', 'PPTX',
  'ODT', 'ODS', 'ODP', 'RTF', 'TXT', 'MD', 'HTML', 'CSV',
];

export function groupDocTargets(catalog: DocCatalog) {
  return {
    common: catalog.targets.filter((t) => t.group === 'common'),
    other: catalog.targets.filter((t) => t.group === 'other'),
  };
}

export function isRasterDocTarget(ext: string): boolean {
  return ['.png', '.jpg', '.jpeg', '.webp'].includes(ext.toLowerCase());
}

export function isPdfTarget(ext: string): boolean {
  return ext.toLowerCase() === '.pdf';
}
