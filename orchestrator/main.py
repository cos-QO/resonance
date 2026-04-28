"""
Orchestrator entry point.
Usage: python -m orchestrator.main
"""
import logging
import signal
import sys
import threading

from .config import load_config
from .poller import Poller

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    try:
        config = load_config()
    except ValueError as e:
        logger.error("configuration error: %s", e)
        sys.exit(1)

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
