import base64
import os
import time
from dataclasses import dataclass
from typing import Iterator, Tuple

import cv2
import numpy as np

@dataclass
class FrameMeta:
    sensor_id: str
    ts: float
    path: str

def _bgr_to_b64(img: np.ndarray, quality: int = 85) -> str:
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        raise ValueError("Failed to encode image")
    return base64.b64encode(buf.tobytes()).decode("ascii")

def frames_from_folder(folder: str, sensor_id: str = "cam-1", max_n: int = 200) -> Iterator[Tuple[str, FrameMeta]]:
    exts = (".jpg",".jpeg",".png",".bmp",".webp")
    paths = []
    for root, _, files in os.walk(folder):
        for fn in files:
            if fn.lower().endswith(exts):
                paths.append(os.path.join(root, fn))
    paths.sort()
    for p in paths[:max_n]:
        img = cv2.imread(p, cv2.IMREAD_COLOR)
        if img is None:
            continue
        b64 = _bgr_to_b64(img)
        yield b64, FrameMeta(sensor_id=sensor_id, ts=time.time(), path=p)
