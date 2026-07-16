#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ImgBatch HTTP API — Tauri sidecar entry.

Run standalone:

    python -m imgbatch.api.main

The first stdout line is::

    IMG_BATCH_PORT=<port>

Tauri parses this to discover the API base URL.
"""

import os
import socket
from contextlib import closing

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from imgbatch.api.routes import backups, config, gif, health, preview, scan, tasks, undo

app = FastAPI(title="ImgBatch API", version="3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # localhost sidecar only — not exposed
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────

app.include_router(health.router)
app.include_router(config.router, prefix="/config")
app.include_router(scan.router)
app.include_router(preview.router, prefix="/preview")
app.include_router(gif.router, prefix="/gif")
app.include_router(tasks.router, prefix="/tasks")
app.include_router(backups.router, prefix="/backups")
app.include_router(undo.router, prefix="/undo")


# ── Port discovery ───────────────────────────────────────────────────────

def find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> None:
    port = int(os.environ.get("IMG_BATCH_PORT", 0)) or find_free_port()
    # Tauri must parse this line from stdout
    print(f"IMG_BATCH_PORT={port}", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
