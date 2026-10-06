"""Cấu hình logging: luôn ghi ra file; chỉ ghi ra terminal khi thật sự có terminal."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging(log_dir: Path) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "refund-agent.log"

    root = logging.getLogger("refund_agent")
    root.setLevel(logging.INFO)
    root.handlers.clear()

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(file_handler)

    # pythonw.exe không có console: sys.stderr là None, thêm StreamHandler sẽ làm crash.
    if sys.stderr is not None:
        stream = logging.StreamHandler()
        stream.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        root.addHandler(stream)

    return log_file
