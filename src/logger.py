import logging
import os
from datetime import datetime

_LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")


def setup_logger() -> None:
    os.makedirs(_LOG_DIR, exist_ok=True)
    log_file = os.path.join(
        _LOG_DIR, f"agent_{datetime.now().strftime('%Y%m%d')}.log"
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )
