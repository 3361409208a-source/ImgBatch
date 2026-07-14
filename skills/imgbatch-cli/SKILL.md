# ImgBatch CLI Skill

## Description
Batch image processing toolkit: compress, convert, rename, watermark, trim, normalize, inspect, and AI-rename images via command line.

## When to Use
Use this skill when the user asks to:
- Batch compress or resize images
- Convert image formats (JPG, PNG, WEBP, BMP, TIFF, GIF, ICO)
- Batch rename images (prefix, suffix, find-replace, sequence, case)
- Add text or image watermarks to images
- Trim transparent edges from PNGs
- Normalize PNG glyph heights
- Inspect PNG canvas/content/padding metrics
- AI-powered smart rename via DeepSeek API

## Prerequisites
- Python 3.7+ with Pillow installed
- The `imgbatch` package must be importable (add project root to PYTHONPATH or install with `pip install -e .`)
- For AI rename: DeepSeek API key

## Commands

### Compress
```bash
python -m imgbatch.cli compress -f ./photos --quality 75 --resize 50
```
Options:
- `--quality` (1-100): JPEG/WebP quality
- `--resize` (1-100): Resize percentage
- `--exif` (keep|strip|orientation_only): EXIF handling
- `-o <dir>`: Output to folder instead of replacing
- `--no-backup`: Disable auto-backup
- `-r`: Include subdirectories
- `--also-convert --to .webp`: Also convert format
- `--also-watermark --watermark-text "© 2026" --watermark-opacity 50`: Also add watermark
- `--also-rename --prefix "photo_"`: Also rename

### Convert
```bash
python -m imgbatch.cli convert -f ./photos --to webp
```

### Rename
```bash
# Sequence mode
python -m imgbatch.cli rename -f ./photos --mode seq --template "photo_{num}" --start 1 --digits 3

# Prefix mode
python -m imgbatch.cli rename -f ./photos --mode prefix --prefix "vacation_"

# Find-replace mode
python -m imgbatch.cli rename -f ./photos --mode replace --find "IMG_" --replace "trip_"

# Dry run (preview only)
python -m imgbatch.cli rename -f ./photos --mode prefix --prefix "test_" --dry-run
```

### Watermark
```bash
# Text watermark
python -m imgbatch.cli watermark -f ./photos --text "© 2026" --opacity 50 --position bottom-right

# Image watermark
python -m imgbatch.cli watermark -f ./photos --image logo.png --scale 20 --opacity 80
```

### Trim Transparent Edges
```bash
python -m imgbatch.cli trim -f ./pngs --padding 4
```

### Normalize PNG Heights
```bash
python -m imgbatch.cli normalize -f ./pngs --target-height 280 --alpha-threshold 28 --padding 6
```

### Inspect PNGs
```bash
python -m imgbatch.cli inspect -f ./pngs
```

### AI Rename (DeepSeek)
```bash
python -m imgbatch.cli ai-rename -f ./photos --api-key sk-xxx --apply
```

## Output
All commands print progress bars and a summary with before/after sizes and error count. Exit code 0 on success, 1 on error.

## Notes
- All operations support `--no-backup` to skip backup creation
- Use `-o <dir>` to output to a separate folder instead of replacing originals
- Recursive scanning with `-r` includes all subdirectories
- Logs are written to `~/.imgbatch/imgbatch.log`

  target_file: c:\Users\Administrator\Desktop\ImgBatch\skills\imgbatch-cli\SKILL.md
  code_edit: # ImgBatch CLI Skill

## Description
Batch image processing toolkit: compress, convert, rename, watermark, trim, normalize, inspect, and AI-rename images via command line.

## When to Use
Use this skill when the user asks to:
- Batch compress or resize images
- Convert image formats (JPG, PNG, WEBP, BMP, TIFF, GIF, ICO)
- Batch rename images (prefix, suffix, find-replace, sequence, case)
- Add text or image watermarks to images
- Trim transparent edges from PNGs
- Normalize PNG glyph heights
- Inspect PNG canvas/content/padding metrics
- AI-powered smart rename via DeepSeek API

## Prerequisites
- Python 3.7+ with Pillow installed
- The `imgbatch` package must be importable (add project root to PYTHONPATH or install with `pip install -e .`)
- For AI rename: DeepSeek API key

## Commands

### Compress
```bash
python -m imgbatch.cli compress -f ./photos --quality 75 --resize 50
```
Options:
- `--quality` (1-100): JPEG/WebP quality
- `--resize` (1-100): Resize percentage
- `--exif` (keep|strip|orientation_only): EXIF handling
- `-o <dir>`: Output to folder instead of replacing
- `--no-backup`: Disable auto-backup
- `-r`: Include subdirectories
- `--also-convert --to .webp`: Also convert format
- `--also-watermark --watermark-text "© 2026" --watermark-opacity 50`: Also add watermark
- `--also-rename --prefix "photo_"`: Also rename

### Convert
```bash
python -m imgbatch.cli convert -f ./photos --to webp
```

### Rename
```bash
# Sequence mode
python -m imgbatch.cli rename -f ./photos --mode seq --template "photo_{num}" --start 1 --digits 3

# Prefix mode
python -m imgbatch.cli rename -f ./photos --mode prefix --prefix "vacation_"

# Find-replace mode
python -m imgbatch.cli rename -f ./photos --mode replace --find "IMG_" --replace "trip_"

# Dry run (preview only)
python -m imgbatch.cli rename -f ./photos --mode prefix --prefix "test_" --dry-run
```

### Watermark
```bash
# Text watermark
python -m imgbatch.cli watermark -f ./photos --text "© 2026" --opacity 50 --position bottom-right

# Image watermark
python -m imgbatch.cli watermark -f ./photos --image logo.png --scale 20 --opacity 80
```

### Trim Transparent Edges
```bash
python -m imgbatch.cli trim -f ./pngs --padding 4
```

### Normalize PNG Heights
```bash
python -m imgbatch.cli normalize -f ./pngs --target-height 280 --alpha-threshold 28 --padding 6
```

### Inspect PNGs
```bash
python -m imgbatch.cli inspect -f ./pngs
```

### AI Rename (DeepSeek)
```bash
python -m imgbatch.cli ai-rename -f ./photos --api-key sk-xxx --apply
```

## Output
All commands print progress bars and a summary with before/after sizes and error count. Exit code 0 on success, 1 on error.

## Notes
- All operations support `--no-backup` to skip backup creation
- Use `-o <dir>` to output to a separate folder instead of replacing originals
- Recursive scanning with `-r` includes all subdirectories
- Logs are written to `~/.imgbatch/imgbatch.log`

