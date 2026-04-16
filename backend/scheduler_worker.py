"""Dedicated scheduler worker entry point for cloud deployments."""

import asyncio
import logging
import os
import signal

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

from core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

from core.scheduler import start_scheduler, stop_scheduler
from core.startup import run_startup_tasks


async def _wait_for_shutdown_signal() -> None:
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            continue

    await stop_event.wait()


async def main() -> None:
    logger.info("🚀 Scheduler worker starting...")

    if not run_startup_tasks():
        logger.warning("Scheduler worker startup tasks reported warnings. Continuing in degraded mode.")

    await start_scheduler()

    try:
        await _wait_for_shutdown_signal()
    finally:
        stop_scheduler()
        logger.info("👋 Scheduler worker shutting down...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scheduler worker interrupted by user")