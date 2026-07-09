import argparse
import os

import uvicorn

DEFAULT_API_WORKERS = 1


def api_worker_count() -> int:
    configured_workers = os.getenv("WEB_CONCURRENCY")
    if configured_workers is None or configured_workers.strip() == "":
        return DEFAULT_API_WORKERS

    try:
        worker_count = int(configured_workers)
    except ValueError as exc:
        raise ValueError("WEB_CONCURRENCY must be a positive integer") from exc

    if worker_count < 1:
        raise ValueError("WEB_CONCURRENCY must be a positive integer")
    return worker_count


def main() -> None:
    parser = argparse.ArgumentParser(prog="backend")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("serve")
    parser.parse_args()

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, workers=api_worker_count())
