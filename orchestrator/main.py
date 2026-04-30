"""
Orchestrator entry point.
Usage: python -m orchestrator.main
"""
import logging
import signal
import sys
from pathlib import Path

from .config import load_config
from .poller import Poller
from . import tracer

_LOG_DIR = Path("runs")
_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Console handler — INFO and above
_console = logging.StreamHandler(sys.stderr)
_console.setLevel(logging.INFO)
_console.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s %(message)s", "%H:%M:%S"))

# File handler — DEBUG and above (persistent dev log)
_file = logging.FileHandler(_LOG_DIR / "orchestrator.log", encoding="utf-8")
_file.setLevel(logging.DEBUG)
_file.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s %(message)s", "%Y-%m-%dT%H:%M:%S"))

logging.root.setLevel(logging.DEBUG)
logging.root.addHandler(_console)
logging.root.addHandler(_file)

logger = logging.getLogger(__name__)


def main() -> None:
    try:
        config = load_config()
    except ValueError as e:
        logger.error("configuration error: %s", e)
        sys.exit(1)

    tracer.load()
    tracer.start_session()

    poller = Poller(config)

    # Graceful shutdown on SIGINT / SIGTERM
    def _shutdown(signum, frame):
        logger.info("shutdown signal received")
        poller.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    poller.run_forever()


if __name__ == "__main__":
    main()
