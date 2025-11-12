"""Junmai AutoDev desktop entry point.

Responsibilities:
1. Start the local_bridge Flask server (in a worker thread).
2. Launch the PyQt6 desktop UI.
3. Coordinate graceful shutdown so no stray processes linger.
"""

from __future__ import annotations

import argparse
import atexit
import logging
import threading
from contextlib import suppress
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Iterable

from werkzeug.serving import make_server

SERVER = None
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = Path.cwd() / "logs"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Junmai AutoDev desktop launcher.")
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip startup filesystem/service checks (used for fast relaunches).",
    )
    return parser.parse_args(argv)


def configure_logging() -> None:
    """Configure root logger with rotating file handler."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )

    file_handler = RotatingFileHandler(
        LOG_DIR / "desktop.log",
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def perform_startup_checks() -> None:
    """Ensure required directories exist before services spin up."""
    jobs_base = BASE_DIR / "local_bridge" / "jobs"
    required_dirs = [
        jobs_base / "inbox",
        jobs_base / "processing",
        jobs_base / "completed",
        jobs_base / "failed",
        LOG_DIR,
    ]

    for directory in required_dirs:
        directory.mkdir(parents=True, exist_ok=True)

    logging.info("Startup checks completed (directories ready).")


def run_server() -> None:
    """Runs the Flask bridge server using Werkzeug's WSGI server."""
    global SERVER
    from local_bridge import app as flask_app_module  # Lazy import for PyInstaller

    logging.info("Starting Junmai AutoDev bridge server on http://127.0.0.1:5100")
    try:
        SERVER = make_server(
            "127.0.0.1",
            5100,
            flask_app_module.app,
        )
        SERVER.serve_forever()
    except Exception as exc:  # pragma: no cover - logged for observability
        logging.exception("Bridge server crashed: %s", exc)


def shutdown_server() -> None:
    """Stops the Werkzeug server when the app exits."""
    global SERVER
    if SERVER is not None:
        logging.info("Shutting down bridge server")
        with suppress(Exception):
            SERVER.shutdown()
        SERVER = None


atexit.register(shutdown_server)


def start_gui() -> int:
    """Creates and runs the PyQt6 desktop application."""
    from gui_qt import main as qt_main  # Imported lazily for PyInstaller

    logging.info("Launching Junmai AutoDev desktop UI")
    return qt_main.launch()


def main(argv: Iterable[str] | None = None) -> int:
    """Entry point used by both python and the packaged executable."""
    args = parse_args(argv)
    configure_logging()

    if not args.skip_checks:
        perform_startup_checks()
    else:
        logging.info("Skipping startup checks (per --skip-checks).")

    server_thread = threading.Thread(target=run_server, daemon=True, name="bridge-server")
    server_thread.start()

    exit_code = start_gui()

    shutdown_server()
    with suppress(Exception):
        if server_thread.is_alive():
            logging.info("Waiting for bridge server to terminate")
            server_thread.join(timeout=2)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
