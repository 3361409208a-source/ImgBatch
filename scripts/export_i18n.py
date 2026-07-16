#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Export i18n translations from imgbatch/infra/i18n.py to frontend JSON files."""

import json
import os
import sys

# Add project root to path
ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, ROOT)

from imgbatch.infra.i18n import TRANSLATIONS

OUTPUT_DIR = os.path.join(ROOT, "frontend", "src", "i18n")

for lang in ("zh", "en"):
    out_path = os.path.join(OUTPUT_DIR, f"{lang}.json")
    data = TRANSLATIONS.get(lang, {})
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Exported {len(data)} keys -> {out_path}")

print("Done.")
