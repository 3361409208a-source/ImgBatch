#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ImgBatch — All-in-One Batch Image Toolkit.

This file is the backward-compatible entry point.
The actual implementation lives in the `imgbatch` package.

Run directly or double-click to launch the GUI:
    python image_compressor.pyw
"""

from imgbatch.ui.app import main

if __name__ == '__main__':
    main()
