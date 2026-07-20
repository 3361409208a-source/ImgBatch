#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Command-line interface for ImgBatch.

Usage examples::

    python -m imgbatch.cli compress --folder ./photos --quality 75 --resize 50
    python -m imgbatch.cli convert --folder ./photos --to webp
    python -m imgbatch.cli rename --folder ./photos --mode seq --template "photo_{num}" --start 1
    python -m imgbatch.cli watermark --folder ./photos --text "© 2026" --opacity 50
    python -m imgbatch.cli trim --folder ./pngs --padding 4
    python -m imgbatch.cli normalize --folder ./pngs --target-height 280
    python -m imgbatch.cli inspect --folder ./pngs
    python -m imgbatch.cli ai-rename --folder ./photos --api-key sk-xxx
"""


import argparse
import os
import sys
import time
from typing import Any

from ..core.common import scan_folder, fmt_size, SUPPORTED_EXT
from ..core.compress import run_compress_batch
from ..core.convert import run_convert_batch
from ..core.rename import generate_rename_map, run_rename_batch, ConflictResolution
from ..core.watermark import run_watermark_batch
from ..core.trim import run_trim_batch
from ..core.normalize import run_normalize_batch
from ..core.inspect import run_inspect_batch
from ..core.spritesheet import run_spritesheet_build, LAYOUTS
from ..core.ai_rename import run_ai_rename, apply_ai_rename, DEFAULT_PROMPT
from ..infra.logger import get_logger
from ..infra.threading import TaskState


class CLITaskState(TaskState):
    """TaskState subclass that prints progress to stdout."""

    def __init__(self):
        super().__init__()
        self._last_pct = -1

    def check_and_print(self, pct: float, msg: str):
        pct_int = int(pct)
        if pct_int != self._last_pct:
            self._last_pct = pct_int
            bar_len = 30
            filled = int(bar_len * pct / 100)
            bar = '=' * filled + '-' * (bar_len - filled)
            sys.stdout.write(f'\r[{bar}] {pct_int}% {msg}')
            sys.stdout.flush()
            if pct_int >= 100:
                sys.stdout.write('\n')


def _on_progress_cli(state: CLITaskState):
    def callback(pct: float, msg: str):
        state.check_and_print(pct, msg)
    return callback


def cmd_compress(args):
    folder = os.path.abspath(args.folder)
    files = scan_folder(folder, recursive=args.recursive)
    if not files:
        print('No supported images found.')
        return 1

    file_list = [f['name'] for f in files]
    print(f'Found {len(file_list)} images in {folder}')

    state = CLITaskState()

    if getattr(args, 'mode', 'normal') == 'balanced':
        from ..core.balanced_compress import run_balanced_compress_batch
        result = run_balanced_compress_batch(
            state, folder, file_list,
            target_mb=args.target_mb,
            do_backup=args.backup, replace=not args.output,
            out=args.output,
            on_progress=_on_progress_cli(state),
        )
        _print_result(result, 'compress')
        if result.get('skipped'):
            print(f"Skipped {len(result['skipped'])} non-animated files.")
        return 0

    options = {}
    if args.also_convert:
        options['convert'] = True
        options['target_fmt'] = args.to
    if args.also_watermark:
        options['watermark'] = True
        options['wm_text'] = args.watermark_text or ''
        options['wm_opacity'] = (args.watermark_opacity or 50) / 100
    if args.also_rename:
        options['rename'] = True
        options['prefix'] = args.prefix or ''
        options['suffix'] = args.suffix or ''

    state = CLITaskState()
    result = run_compress_batch(
        state, folder, file_list,
        quality=args.quality, resize_pct=args.resize,
        do_backup=args.backup, replace=not args.output,
        out=args.output, exif_mode=args.exif,
        options=options,
        on_progress=_on_progress_cli(state),
    )

    _print_result(result, 'compress')
    return 0


def cmd_convert(args):
    folder = os.path.abspath(args.folder)
    files = scan_folder(folder, recursive=args.recursive)
    if not files:
        print('No supported images found.')
        return 1

    file_list = [f['name'] for f in files]
    print(f'Found {len(file_list)} images in {folder}')

    state = CLITaskState()
    result = run_convert_batch(
        state, folder, file_list, args.to,
        args.backup, not args.output, args.output,
        on_progress=_on_progress_cli(state),
    )
    _print_result(result, 'convert')
    return 0


def cmd_rename(args):
    folder = os.path.abspath(args.folder)
    files = scan_folder(folder, recursive=args.recursive)
    if not files:
        print('No supported images found.')
        return 1

    mapping = generate_rename_map(
        files, args.mode,
        prefix=args.prefix or '', suffix=args.suffix or '',
        find=args.find or '', replace=args.replace or '',
        seq_template=args.template or 'photo_{num}',
        seq_start=args.start or 1, seq_digits=args.digits or 3,
        lowercase=args.lower, uppercase=args.upper,
    )
    if not mapping:
        print('No files to rename.')
        return 0

    print(f'Will rename {len(mapping)} files:')
    for old, new in list(mapping.items())[:10]:
        print(f'  {old} -> {new}')
    if len(mapping) > 10:
        print(f'  ... and {len(mapping) - 10} more')

    if args.dry_run:
        print('(dry run, no changes made)')
        return 0

    state = CLITaskState()
    result = run_rename_batch(
        state, folder, mapping, ConflictResolution.AUTO_NUMBER,
        on_progress=_on_progress_cli(state),
    )
    print(f'\nRenamed: {result["renamed"]}, Skipped: {result["skipped"]}')
    if result['errors']:
        print(f'Errors: {len(result["errors"])}')
        for e in result['errors'][:5]:
            print(f'  {e}')
    return 0


def cmd_watermark(args):
    folder = os.path.abspath(args.folder)
    files = scan_folder(folder, recursive=args.recursive)
    if not files:
        print('No supported images found.')
        return 1

    file_list = [f['name'] for f in files]
    print(f'Found {len(file_list)} images in {folder}')

    params = {
        'type': 'image' if args.image else 'text',
        'text': args.text or '',
        'fontsize': args.fontsize or 36,
        'opacity': (args.opacity or 50) / 100,
        'position': args.position or 'bottom-right',
        'color': args.color or '#ffffff',
        'image_path': args.image or '',
        'img_scale': (args.scale or 20) / 100,
    }

    state = CLITaskState()
    result = run_watermark_batch(
        state, folder, file_list, params,
        args.backup, not args.output, args.output,
        on_progress=_on_progress_cli(state),
    )
    _print_result(result, 'watermark')
    return 0


def cmd_trim(args):
    from ..core.common import TRIM_SUPPORTED_EXT

    folder = os.path.abspath(args.folder)
    files = scan_folder(folder, recursive=args.recursive)
    trim_files = [
        f['name'] for f in files
        if os.path.splitext(f['name'])[1].lower() in TRIM_SUPPORTED_EXT
    ]
    if not trim_files:
        print('No trim-compatible image files found (PNG, WebP, GIF, TIFF, ICO, AVIF).')
        return 1

    print(f'Found {len(trim_files)} trim-compatible files in {folder}')

    state = CLITaskState()
    result = run_trim_batch(
        state, folder, trim_files,
        args.padding, args.backup, not args.output, args.output,
        on_progress=_on_progress_cli(state),
    )
    _print_result(result, 'trim')
    return 0


def cmd_normalize(args):
    folder = os.path.abspath(args.folder)
    files = scan_folder(folder, recursive=args.recursive)
    png_files = [f['name'] for f in files if f['name'].lower().endswith('.png')]
    if not png_files:
        print('No PNG files found.')
        return 1

    print(f'Found {len(png_files)} PNG files in {folder}')

    state = CLITaskState()
    result = run_normalize_batch(
        state, folder, png_files,
        args.alpha_threshold, args.target_height, args.padding,
        args.backup, not args.output, args.output,
        on_progress=_on_progress_cli(state),
    )
    _print_result(result, 'normalize')
    return 0


def cmd_inspect(args):
    folder = os.path.abspath(args.folder)
    files = scan_folder(folder, recursive=args.recursive)
    png_files = [f for f in files if f['name'].lower().endswith('.png')]
    if not png_files:
        print('No PNG files found.')
        return 1

    print(f'Found {len(png_files)} PNG files in {folder}\n')
    print(f'{"Name":<30} {"Canvas":<12} {"Content":<12} {"T":>5} {"B":>5} {"L":>5} {"R":>5}')
    print('-' * 80)

    state = CLITaskState()
    result = run_inspect_batch(state, png_files)

    for info in result.get('results', []):
        print(f'{info["name"]:<30} {info["canvas"]:<12} {info["content"]:<12} '
              f'{info["top_pad"]:>5} {info["bot_pad"]:>5} {info["left_pad"]:>5} {info["right_pad"]:>5}')

    if result.get('errors'):
        print(f'\nErrors: {len(result["errors"])}')
    return 0


def cmd_spritesheet(args):
    folder = os.path.abspath(args.folder)
    files = scan_folder(folder, recursive=args.recursive)
    if not files:
        print('No supported images found.')
        return 1

    file_list = [f['name'] for f in files]
    image_paths = [os.path.join(folder, name) for name in file_list]
    output = args.output or os.path.join(folder, 'spritesheet.png')

    print(f'Building sprite sheet from {len(image_paths)} images...')
    state = CLITaskState()
    result = run_spritesheet_build(
        state, image_paths, output,
        layout=args.layout,
        spacing=args.spacing,
        trim=not args.no_trim,
        trim_padding=args.trim_padding,
        alpha_threshold=args.alpha_threshold,
        columns=args.columns,
        max_width=args.max_width,
        power_of_two=args.power_of_two,
        export_json=not args.no_json,
        on_progress=_on_progress_cli(state),
    )

    if result.get('cancelled'):
        print('Sprite sheet build cancelled.')
        return 1

    errors = result.get('errors', [])
    if errors and not result.get('output_path'):
        print('Sprite sheet build failed:')
        for e in errors:
            print(f'  {e}')
        return 1

    w, h = result.get('sheet_size', (0, 0))
    n = result.get('frame_count', 0)
    print(f'\nSprite sheet complete: {w}x{h}, {n} frames')
    print(f'  Output: {result.get("output_path")}')
    if result.get('json_path'):
        print(f'  JSON:   {result.get("json_path")}')
    if errors:
        print(f'  Warnings: {len(errors)}')
        for e in errors[:5]:
            print(f'    {e}')
    return 0


def cmd_ai_rename(args):
    folder = os.path.abspath(args.folder)
    files = scan_folder(folder, recursive=args.recursive)
    if not files:
        print('No supported images found.')
        return 1

    file_names = [f['name'] for f in files]
    print(f'Found {len(file_names)} images in {folder}')
    print(f'Calling DeepSeek API...')

    state = CLITaskState()
    prompt = args.prompt or DEFAULT_PROMPT
    result = run_ai_rename(state, args.api_key, file_names, prompt)

    suggestions = result.get('results', {})
    tokens = result.get('total_tokens', 0)
    errors = result.get('errors', [])

    print(f'\nAI suggestions ({len(suggestions)} names, {tokens} tokens):')
    for orig, sugg in suggestions.items():
        print(f'  {orig} -> {sugg}')

    if errors:
        print(f'\nErrors: {len(errors)}')
        for e in errors[:5]:
            print(f'  {e}')

    if args.apply:
        print('\nApplying renames...')
        state2 = CLITaskState()
        rename_result = apply_ai_rename(state2, folder, suggestions,
                                        on_progress=_on_progress_cli(state2))
        print(f'\nRenamed: {rename_result["renamed"]}')
        if rename_result['errors']:
            print(f'Errors: {len(rename_result["errors"])}')

    return 0


def _print_result(result: dict, op_name: str):
    """Print operation result summary."""
    total_before = result.get('total_before', 0)
    total_after = result.get('total_after', 0)
    errors = result.get('errors', [])
    cancelled = result.get('cancelled', False)

    if cancelled:
        print(f'\n{op_name} cancelled.')
    else:
        saved = total_before - total_after
        print(f'\n{op_name} complete:')
        print(f'  Before: {fmt_size(total_before)}')
        print(f'  After:  {fmt_size(total_after)}')
        print(f'  Saved:  {fmt_size(saved)}')

    if errors:
        print(f'  Errors: {len(errors)}')
        for e in errors[:5]:
            print(f'    {e}')


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='imgbatch',
        description='ImgBatch — All-in-One Batch Image Toolkit',
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Common folder argument
    def add_folder(p):
        p.add_argument('--folder', '-f', required=True, help='Target folder')
        p.add_argument('--recursive', '-r', action='store_true', help='Include subdirectories')
        p.add_argument('--output', '-o', help='Output folder (default: replace original)')
        p.add_argument('--backup', action='store_true', default=True, help='Enable backup')
        p.add_argument('--no-backup', dest='backup', action='store_false', help='Disable backup')

    # compress
    p = subparsers.add_parser('compress', help='Batch compress images')
    add_folder(p)
    p.add_argument('--quality', type=int, default=75, help='Quality 1-100 (default: 75)')
    p.add_argument('--resize', type=int, default=100, help='Resize %% 1-100 (default: 100)')
    p.add_argument('--exif', choices=['keep', 'strip', 'orientation_only'], default='keep',
                   help='EXIF mode (default: keep)')
    p.add_argument('--mode', choices=['normal', 'balanced'], default='normal',
                   help='Compression mode (balanced = target size for animated WebP/GIF)')
    p.add_argument('--target-mb', type=float, default=1.15,
                   help='Target file size in MB for balanced mode (default: 1.15)')
    p.add_argument('--also-convert', action='store_true', help='Also convert format')
    p.add_argument('--to', default='.png', help='Target format for --also-convert')
    p.add_argument('--also-watermark', action='store_true', help='Also add watermark')
    p.add_argument('--watermark-text', help='Watermark text')
    p.add_argument('--watermark-opacity', type=int, help='Watermark opacity 10-100')
    p.add_argument('--also-rename', action='store_true', help='Also rename')
    p.add_argument('--prefix', help='Rename prefix')
    p.add_argument('--suffix', help='Rename suffix')
    p.set_defaults(func=cmd_compress)

    # convert
    p = subparsers.add_parser('convert', help='Batch convert image format')
    add_folder(p)
    p.add_argument('--to', required=True, help='Target format (e.g. .png, .webp)')
    p.set_defaults(func=cmd_convert)

    # rename
    p = subparsers.add_parser('rename', help='Batch rename images')
    p.add_argument('--folder', '-f', required=True, help='Target folder')
    p.add_argument('--recursive', '-r', action='store_true', help='Include subdirectories')
    p.add_argument('--mode', required=True,
                   choices=['prefix', 'suffix', 'replace', 'seq', 'case'],
                   help='Rename mode')
    p.add_argument('--prefix', help='Prefix to add')
    p.add_argument('--suffix', help='Suffix to add')
    p.add_argument('--find', help='Text to find (replace mode)')
    p.add_argument('--replace', help='Replacement text (replace mode)')
    p.add_argument('--template', help='Sequence template (seq mode, use {num})')
    p.add_argument('--start', type=int, help='Sequence start number')
    p.add_argument('--digits', type=int, help='Sequence digit count')
    p.add_argument('--lower', action='store_true', help='Lowercase (case mode)')
    p.add_argument('--upper', action='store_true', help='Uppercase (case mode)')
    p.add_argument('--dry-run', action='store_true', help='Preview without changes')
    p.set_defaults(func=cmd_rename)

    # watermark
    p = subparsers.add_parser('watermark', help='Batch add watermark')
    add_folder(p)
    p.add_argument('--text', help='Watermark text (text mode)')
    p.add_argument('--image', help='Watermark image path (image mode)')
    p.add_argument('--fontsize', type=int, help='Font size (text mode)')
    p.add_argument('--opacity', type=int, help='Opacity 10-100')
    p.add_argument('--position', choices=['top-left', 'top-right', 'center', 'bottom-left', 'bottom-right'],
                   help='Position')
    p.add_argument('--color', help='Text color #RRGGBB (text mode)')
    p.add_argument('--scale', type=int, help='Image scale %% (image mode)')
    p.set_defaults(func=cmd_watermark)

    # trim
    p = subparsers.add_parser('trim', help='Trim transparent edges (PNG, WebP, etc.)')
    add_folder(p)
    p.add_argument('--padding', type=int, default=4, help='Padding pixels (default: 4)')
    p.set_defaults(func=cmd_trim)

    # normalize
    p = subparsers.add_parser('normalize', help='Normalize PNG glyph heights')
    add_folder(p)
    p.add_argument('--alpha-threshold', type=int, default=28, help='Alpha threshold (default: 28)')
    p.add_argument('--target-height', type=int, default=280, help='Target content height (default: 280)')
    p.add_argument('--padding', type=int, default=6, help='Padding pixels (default: 6)')
    p.set_defaults(func=cmd_normalize)

    # inspect
    p = subparsers.add_parser('inspect', help='Inspect PNG canvas/content/padding')
    p.add_argument('--folder', '-f', required=True, help='Target folder')
    p.add_argument('--recursive', '-r', action='store_true', help='Include subdirectories')
    p.set_defaults(func=cmd_inspect)

    # spritesheet
    p = subparsers.add_parser('spritesheet', help='Build a smart sprite sheet atlas')
    p.add_argument('--folder', '-f', required=True, help='Target folder')
    p.add_argument('--recursive', '-r', action='store_true', help='Include subdirectories')
    p.add_argument('--output', '-o', help='Output PNG path (default: folder/spritesheet.png)')
    p.add_argument('--layout', choices=LAYOUTS, default='auto',
                   help='Layout mode (default: auto)')
    p.add_argument('--spacing', type=int, default=2, help='Spacing pixels (default: 2)')
    p.add_argument('--no-trim', action='store_true', help='Disable auto-trim transparent edges')
    p.add_argument('--trim-padding', type=int, default=2, help='Trim padding (default: 2)')
    p.add_argument('--alpha-threshold', type=int, default=28, help='Alpha threshold (default: 28)')
    p.add_argument('--columns', type=int, default=0, help='Grid columns, 0=auto (default: 0)')
    p.add_argument('--max-width', type=int, default=0, help='Max row width, 0=smart (default: 0)')
    p.add_argument('--power-of-two', action='store_true', help='Round canvas to power-of-2')
    p.add_argument('--no-json', action='store_true', help='Skip JSON metadata export')
    p.set_defaults(func=cmd_spritesheet)

    # ai-rename
    p = subparsers.add_parser('ai-rename', help='AI-powered rename via DeepSeek')
    p.add_argument('--folder', '-f', required=True, help='Target folder')
    p.add_argument('--recursive', '-r', action='store_true', help='Include subdirectories')
    p.add_argument('--api-key', required=True, help='DeepSeek API key')
    p.add_argument('--prompt', help='Custom prompt')
    p.add_argument('--apply', action='store_true', help='Apply suggested renames')
    p.set_defaults(func=cmd_ai_rename)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    get_logger().info("CLI command: %s", args.command)
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
