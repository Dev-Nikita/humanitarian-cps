#!/usr/bin/env bash
set -euo pipefail

mkdir -p data/coco/annotations
cd data/coco/annotations

URL="http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
OUT="annotations_trainval2017.zip"

if [ -f "$OUT" ]; then
  echo "Already downloaded: $OUT"
else
  echo "Downloading COCO annotations zip..."
  curl -L "$URL" -o "$OUT"
fi

echo "Unzipping..."
unzip -o "$OUT"

echo "Done. Download images separately and place them under data/coco/images/val2017/"
