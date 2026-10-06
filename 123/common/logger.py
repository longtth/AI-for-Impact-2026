"""Log luôn ghi ra file; chỉ thêm console handler khi có stderr (pythonw.exe không có)."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from common.config import APP_NAME

_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging(log_dir: Path, console: bool = True) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{APP_NAME}.log"
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for h in list(root.handlers):
        root.removeHandler(h)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(_FORMAT))
    root.addHandler(file_handler)
    if console and sys.stderr is not None:
        stream = logging.StreamHandler()
        stream.setFormatter(logging.Formatter(_FORMAT))
        root.addHandler(stream)
    logging.getLogger(__name__).info("Ghi log vào file: %s", log_file)
    return log_file
