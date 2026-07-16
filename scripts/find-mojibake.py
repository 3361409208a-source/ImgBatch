#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

root = r"C:\Users\Administrator\Desktop\ImgBatch\frontend\src"
for dp, _, fs in os.walk(root):
    for f in fs:
        if not f.endswith((".tsx", ".ts", ".css", ".json")):
            continue
        p = os.path.join(dp, f)
        data = open(p, "rb").read()
        if b"\xef\xbf\xbd" in data:
            print("REPLACEMENT:", p)
        text = data.decode("utf-8", "replace")
        if "\ufffd" in text:
            print("UFFFD:", p)
            for i, line in enumerate(text.splitlines(), 1):
                if "\ufffd" in line:
                    print(f"  L{i}: {line[:120]}")
