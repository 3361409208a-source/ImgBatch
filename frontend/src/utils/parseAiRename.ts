/** Client-side AI rename JSON parser (mirrors imgbatch.core.ai_rename.parse_ai_rename_response). */

function sanitizeFilename(name: string): string {
  if (!name) return name;
  let n = name.replace(/[<>:"/\\|?*]/g, '');
  n = n.replace(/[\x00-\x1f]/g, '');
  n = n.replace(/^[.\s]+|[.\s]+$/g, '');
  n = n.replace(/\{/g, '').replace(/\}/g, '').replace(/'/g, '').replace(/"/g, '');
  return n;
}

export function parseAiRenameLocally(
  content: string,
  fileNames: string[],
): { mapping: Record<string, string>; errors: string[] } {
  if (!content.trim()) {
    return { mapping: {}, errors: ['Empty content'] };
  }
  if (fileNames.length === 0) {
    return { mapping: {}, errors: ['Empty file list'] };
  }

  const jsonMatch = content.match(/\[[\s\S]*\]/);
  let resultList: unknown[] | null = null;

  if (jsonMatch) {
    try {
      resultList = JSON.parse(jsonMatch[0]) as unknown[];
    } catch {
      /* try line fallback below */
    }
  }

  if (!resultList) {
    const lines = content
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean);
    resultList = lines.length > 0 ? lines : [content.trim()];
  }

  if (!Array.isArray(resultList)) {
    resultList = [resultList];
  }

  const mapping: Record<string, string> = {};

  resultList.forEach((item, i) => {
    if (item && typeof item === 'object' && !Array.isArray(item)) {
      const row = item as Record<string, unknown>;
      const orig = String(row.original ?? '');
      const suggested = String(row.new ?? row.new_name ?? row.suggested ?? '');
      if (orig && fileNames.includes(orig)) {
        mapping[orig] = sanitizeFilename(suggested) || orig;
      } else if (i < fileNames.length) {
        mapping[fileNames[i]] = sanitizeFilename(suggested) || fileNames[i];
      }
    } else if (typeof item === 'string' && i < fileNames.length) {
      mapping[fileNames[i]] = sanitizeFilename(item) || fileNames[i];
    }
  });

  for (const fn of fileNames) {
    if (!(fn in mapping)) mapping[fn] = fn;
  }

  const hasChanges = Object.entries(mapping).some(([orig, next]) => orig !== next);
  if (!hasChanges) {
    return {
      mapping,
      errors: ['Could not parse any rename suggestions from the pasted text'],
    };
  }

  return { mapping, errors: [] };
}
