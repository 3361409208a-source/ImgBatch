#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""AI-powered rename via DeepSeek API.

Features:
- Exponential backoff retry (3 attempts)
- Response structure validation
- Batch sending (max 100 filenames per request)
- Token usage tracking
"""


import ast
import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Callable, Dict, List, Optional, Tuple

from .rename import sanitize_filename
from ..infra.logger import get_logger

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
MAX_BATCH = 100
MAX_RETRIES = 3
RETRY_DELAYS = [1.0, 2.0, 4.0]  # seconds
DEFAULT_USER_PROMPT = (
    "\u4e3a\u6bcf\u4e2a\u56fe\u7247\u751f\u6210\u7b80\u6d01\u89c4\u8303\u7684\u82f1\u6587\u6587\u4ef6\u540d"
    "\uff08\u4fdd\u7559\u6269\u5c55\u540d\uff09\uff0c"
    "\u4f8b\u5982 player_name-position-country.jpg\u3002"
)
# Backward-compatible alias used by CLI / legacy UI.
DEFAULT_PROMPT = DEFAULT_USER_PROMPT

_USER_MESSAGE_FORMAT = (
    "\n\nReturn only a JSON array (double quotes). "
    'Each item: {"original": "filename", "new": "newname"}. '
    "No other text."
)


def build_ai_user_message(user_prompt: str, file_names: List[str]) -> str:
    """Combine user instruction, file list, and internal format constraints."""
    instruction = (user_prompt or DEFAULT_USER_PROMPT).strip()
    files = "\n".join(file_names)
    return f"{instruction}\n\nName list:\n{files}{_USER_MESSAGE_FORMAT}"
SYSTEM_PROMPT = (
    "You are a file naming assistant. "
    "Return a standard JSON array (double quotes). "
    'Format: Each element: {"original": "name", "new": "newname"}.'
)


class AIError(Exception):
    """Raised when the AI rename operation fails."""


class AIResponseError(AIError):
    """Raised when the API response is malformed."""


class AIApiError(AIError):
    """Raised when the API returns an error status."""

    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


def _call_deepseek(
    api_key: str,
    file_names: List[str],
    prompt: str,
    timeout: int = 60,
) -> Tuple[List[dict], dict]:
    """Call DeepSeek API with retry logic.

    Returns (result_list, usage_info).
    Raises AIApiError or AIResponseError.
    """
    logger = get_logger()
    last_exc: Optional[Exception] = None

    req_body = json.dumps({
        'model': DEEPSEEK_MODEL,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': build_ai_user_message(prompt, file_names)},
        ],
        'temperature': 0.7,
        'max_tokens': 4096,
    }).encode('utf-8')

    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(
                DEEPSEEK_API_URL,
                data=req_body,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}',
                },
            )
            resp = urllib.request.urlopen(req, timeout=timeout)
            data = json.loads(resp.read().decode('utf-8'))

            # Validate response structure
            if 'error' in data:
                err_msg = data['error'].get('message', 'Unknown API error')
                # Don't leak the API key in error messages
                err_msg = err_msg.replace(api_key, '***')
                raise AIApiError(err_msg)

            choices = data.get('choices', [])
            if not choices:
                raise AIResponseError("API returned empty choices array")

            content = choices[0].get('message', {}).get('content', '').strip()
            if not content:
                raise AIResponseError("API returned empty content")

            usage = data.get('usage', {})

            # Parse the response content as JSON
            result_list = _parse_ai_response(content, file_names)
            return result_list, usage

        except urllib.error.HTTPError as exc:
            last_exc = exc
            status = exc.code
            try:
                body = json.loads(exc.read().decode('utf-8'))
                msg = body.get('error', {}).get('message', str(exc))
                msg = msg.replace(api_key, '***')
            except (json.JSONDecodeError, UnicodeDecodeError):
                msg = str(exc)

            if status == 429 or status >= 500:
                # Retryable: rate limit or server error
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                logger.warning("API retryable error (status %d): %s. Waiting %.1fs", status, msg, delay)
                time.sleep(delay)
                continue
            else:
                raise AIApiError(msg, status_code=status)

        except urllib.error.URLError as exc:
            last_exc = exc
            delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
            logger.warning("Network error: %s. Waiting %.1fs", exc, delay)
            time.sleep(delay)
            continue

    # All retries exhausted
    if last_exc:
        raise AIApiError(f"API call failed after {MAX_RETRIES} attempts: {last_exc}")
    raise AIApiError(f"API call failed after {MAX_RETRIES} attempts")


def _parse_ai_response(content: str, file_names: List[str]) -> List[dict]:
    """Parse AI response content into a list of {original, new} dicts.

    Tries JSON first, then ast.literal_eval, then line-by-line fallback.
    """
    # Try to extract a JSON array from the content
    json_match = re.search(r'\[.*\]', content, re.DOTALL)
    result_list = None

    if json_match:
        try:
            result_list = json.loads(json_match.group())
        except (json.JSONDecodeError, ValueError):
            pass

    if result_list is None and json_match:
        try:
            result_list = ast.literal_eval(json_match.group())
        except (ValueError, SyntaxError):
            pass

    if result_list is None:
        # Fallback: split by lines
        result_list = [line.strip() for line in content.splitlines() if line.strip()]
        if not result_list:
            result_list = [content]

    if not isinstance(result_list, list):
        result_list = [result_list]

    # Normalize to list of dicts
    normalized: List[dict] = []
    for i, item in enumerate(result_list):
        if isinstance(item, dict):
            orig = item.get('original', '')
            new_name = item.get('new', item.get('new_name', item.get('suggested', '')))
            if orig and orig in file_names:
                normalized.append({'original': orig, 'new': sanitize_filename(new_name) or orig})
            else:
                # Try to match by position
                if i < len(file_names):
                    normalized.append({
                        'original': file_names[i],
                        'new': sanitize_filename(new_name) or file_names[i],
                    })
        elif isinstance(item, str) and i < len(file_names):
            normalized.append({
                'original': file_names[i],
                'new': sanitize_filename(item) or file_names[i],
            })

    return normalized


def parse_ai_rename_response(content: str, file_names: List[str]) -> Dict[str, str]:
    """Parse pasted AI text into original -> suggested name mapping."""
    items = _parse_ai_response(content, file_names)
    results: Dict[str, str] = {}
    for item in items:
        results[item['original']] = item['new']
    for fn in file_names:
        if fn not in results:
            results[fn] = fn
    return results


def run_ai_rename(
    state,
    api_key: str,
    file_names: List[str],
    prompt: str,
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_batch_done: Optional[Callable[[List[dict], dict], None]] = None,
) -> dict:
    """Run AI rename analysis with batching and retry.

    Returns dict with:
        results: Dict[original_name -> suggested_name]
        total_tokens: int
        errors: List[str]
        cancelled: bool
    """
    logger = get_logger()
    results: Dict[str, str] = {}
    total_tokens = 0
    errors: List[str] = []

    # Process in batches
    batches = [file_names[i:i + MAX_BATCH] for i in range(0, len(file_names), MAX_BATCH)]
    total_batches = len(batches)

    for batch_idx, batch in enumerate(batches):
        if state.cancelled:
            break

        try:
            batch_results, usage = _call_deepseek(api_key, batch, prompt)
            total_tokens += usage.get('total_tokens', 0)

            for item in batch_results:
                results[item['original']] = item['new']

            if on_batch_done:
                on_batch_done(batch_results, usage)

            logger.info(
                "AI batch %d/%d: %d names, %d tokens",
                batch_idx + 1, total_batches, len(batch_results),
                usage.get('total_tokens', 0),
            )

        except (AIApiError, AIResponseError) as exc:
            errors.append(f'Batch {batch_idx + 1}: {exc}')
            logger.error("AI batch %d failed: %s", batch_idx + 1, exc)

        if on_progress:
            pct = (batch_idx + 1) / total_batches * 100
            on_progress(pct, f'Batch {batch_idx + 1}/{total_batches}')

    # Fill in any missing files with their original names
    for fn in file_names:
        if fn not in results:
            results[fn] = fn

    return {
        'results': results,
        'total_tokens': total_tokens,
        'errors': errors,
        'cancelled': state.cancelled,
    }


def apply_ai_rename(
    state,
    folder: str,
    mapping: Dict[str, str],
    on_progress: Optional[Callable[[float, str], None]] = None,
) -> dict:
    """Apply AI-suggested renames to files.

    Returns dict with renamed, errors, cancelled.
    """
    from .rename import run_rename_batch, ConflictResolution

    # Ensure all suggested names have extensions
    clean_mapping: Dict[str, str] = {}
    for orig, sugg in mapping.items():
        if not sugg or not isinstance(sugg, str):
            continue
        if '.' not in sugg:
            sugg = sugg + os.path.splitext(orig)[1]
        orig_ext = os.path.splitext(orig)[1]
        sugg_base = os.path.splitext(sugg)[0]
        new_name = sanitize_filename(sugg_base) + orig_ext
        if new_name != orig:
            clean_mapping[orig] = new_name

    if not clean_mapping:
        return {'renamed': 0, 'errors': [], 'cancelled': False}

    result = run_rename_batch(
        state, folder, clean_mapping,
        conflict_resolution=ConflictResolution.AUTO_NUMBER,
        on_progress=on_progress,
    )
    return {
        'renamed': result['renamed'],
        'errors': result['errors'],
        'cancelled': result['cancelled'],
    }
