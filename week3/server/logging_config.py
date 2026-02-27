import logging
import sys


def configure_logging() -> None:
    """Configure basic logging to stderr to avoid polluting STDIO protocol."""

    handler = logging.StreamHandler(stream=sys.stderr)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # Avoid adding multiple handlers if configure_logging is called more than once.
    if not root.handlers:
        root.addHandler(handler)

