import base64
import time
from dataclasses import dataclass
from typing import Iterator, Tuple

import cv2
import numpy as np

@dataclass
class FrameMeta:
    sensor_id: str
    ts: float

def _bgr_to_b64(img: np.ndarray, quality: int = 85) -> str:
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        raise ValueError("Failed to encode image")
    return base64.b64encode(buf.tobytes()).decode("ascii")

def synthetic_frames(sensor_id: str, n: int = 50, w: int = 640, h: int = 360) -> Iterator[Tuple[str, FrameMeta]]:
    for i in range(n):
        img = np.zeros((h, w, 3), dtype=np.uint8)
        # draw a moving rectangle to mimic "object"
        x = int((i * 10) % (w - 80))
        cv2.rectangle(img, (x, 120), (x + 60, 220), (255, 255, 255), -1)
        cv2.putText(img, f"{sensor_id} frame={i}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        b64 = _bgr_to_b64(img)
        yield b64, FrameMeta(sensor_id=sensor_id, ts=time.time())
