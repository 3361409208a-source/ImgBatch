/** User-editable naming instruction only — no JSON / format constraints. */
export const DEFAULT_USER_PROMPT_ZH =
  '将图片文件名改为简洁英文，保留原扩展名，例如 player_name-position-country.jpg';

export const DEFAULT_USER_PROMPT_EN =
  'Rename image files to concise English names, keep extensions, e.g. player_name-position-country.jpg';

/** Internal block appended when copying to Metaso or calling external AI. */
const RESPONSE_FORMAT_BLOCK = [
  '【返回格式要求 — 系统自动附加，请勿修改】',
  '请只返回 JSON 数组，不要其他说明文字。',
  'Return a JSON array only, no extra text.',
  'Each item: {"original": "原文件名", "new": "新文件名"}',
  'Example: [{"original": "a.jpg", "new": "player_01.jpg"}]',
].join('\n');

/** Full payload for clipboard / external AI (user prompt + files + hidden constraints). */
export function buildExternalAiRenamePrompt(
  userPrompt: string,
  fileNames: string[],
  fallbackPrompt = DEFAULT_USER_PROMPT_ZH,
): string {
  const instruction = userPrompt.trim() || fallbackPrompt.trim();
  return [
    instruction,
    '',
    '【文件列表 / File list】',
    ...fileNames,
    '',
    RESPONSE_FORMAT_BLOCK,
  ].join('\n');
}
