#!/bin/bash
# StoreMind — process all CCTV clips and feed events into API
# Usage: bash pipeline/run.sh [data_dir] [api_url]
set -e

DATA_DIR="${1:-./data}"
API_URL="${2:-http://localhost:8000}"
LAYOUT="${DATA_DIR}/store_layout.json"

echo "=== StoreMind Detection Pipeline ==="
echo "Data dir: $DATA_DIR"
echo "API:      $API_URL"

CLIPS=(
  "STORE_BLR_002 CAM_ENTRY_01 entry"
  "STORE_BLR_002 CAM_FLOOR_01 floor"
  "STORE_BLR_002 CAM_BILLING_01 billing"
)

for CLIP_INFO in "${CLIPS[@]}"; do
  read -r STORE_ID CAMERA_ID CAM_TYPE <<< "$CLIP_INFO"
  VIDEO="${DATA_DIR}/clips/${STORE_ID}_${CAM_TYPE}.mp4"
  OUTPUT="${DATA_DIR}/events/${STORE_ID}_${CAMERA_ID}.jsonl"

  if [ ! -f "$VIDEO" ]; then
    echo "Video not found: $VIDEO — generating mock events"
    VIDEO="__mock__"
  fi

  echo ""
  echo "--- Processing: $STORE_ID / $CAMERA_ID ---"
  python pipeline/detect.py \
    --video "$VIDEO" \
    --store-id "$STORE_ID" \
    --camera-id "$CAMERA_ID" \
    --layout "$LAYOUT" \
    --output "$OUTPUT" \
    --clip-start "2026-03-03T09:00:00"

  # Ingest into API in batches of 500
  if [ -f "$OUTPUT" ]; then
    echo "Ingesting events from $OUTPUT → $API_URL/events/ingest"
    python pipeline/ingest.py --events "$OUTPUT" --api "$API_URL"
  fi
done

echo ""
echo "=== Pipeline complete. Check: $API_URL/stores/STORE_BLR_002/metrics ==="
