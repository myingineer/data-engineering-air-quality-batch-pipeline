import logging
from pathlib import Path


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "pipeline.log"


def setup_logging():
    """
    Configure application logging to both the console
    and a persistent log file.
    """

    # Make sure the logs directory exists.
    LOG_DIR.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(),
        ],
    )