"""
StoreMind — Event Ingestion Script
Reads a .jsonl file and POST /events/ingest in batches of 500.
Idempotent: safe to run multiple times.
"""

import json
import time
import argparse
import logging
import requests
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("storemind.ingest")

BATCH_SIZE = 500


def ingest(events_path: str, api_url: str):
    lines = Path(events_path).read_text().strip().splitlines()
    events = [json.loads(l) for l in lines if l.strip()]
    logger.info(f"Loaded {len(events)} events from {events_path}")

    total_ok, total_fail = 0, 0
    for i in range(0, len(events), BATCH_SIZE):
        batch = events[i:i + BATCH_SIZE]
        try:
            r = requests.post(
                f"{api_url}/events/ingest",
                json={"events": batch},
                timeout=30,
            )
            data = r.json()
            ok = data.get("accepted", len(batch))
            fail = data.get("rejected", 0)
            total_ok += ok
            total_fail += fail
            logger.info(f"Batch {i//BATCH_SIZE + 1}: {ok} accepted, {fail} rejected | HTTP {r.status_code}")
        except Exception as e:
            logger.error(f"Batch {i//BATCH_SIZE + 1} failed: {e}")
            time.sleep(2)

    logger.info(f"Ingestion complete: {total_ok} accepted, {total_fail} rejected")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True)
    parser.add_argument("--api", default="http://localhost:8000")
    args = parser.parse_args()
    ingest(args.events, args.api)
