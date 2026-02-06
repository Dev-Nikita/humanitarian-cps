import os
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from preprocess.preprocess import preprocess

APP = FastAPI(title="edge-inference", version="0.1.0")

ENABLE_FACE_BLUR = os.getenv("ENABLE_FACE_BLUR", "true").lower() == "true"
INFER_ADDR = os.getenv("INFER_ADDR", "0.0.0.0:8001")

# OpenCV HOG person detector (no external weights download)
HOG = cv2.HOGDescriptor()
HOG.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

class InferRequest(BaseModel):
    image_b64: str = Field(..., description="Base64-encoded JPG/PNG")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Detection(BaseModel):
    label: str
    bbox: List[int]  # [x,y,w,h]
    confidence: float

class InferResponse(BaseModel):
    sensor_id: str
    ts: float
    detections: List[Detection]
    latency_ms: float
    preprocess_ms: float
    infer_ms: float

@APP.get("/healthz")
def healthz():
    return {"ok": True}

def detect_people(img: np.ndarray) -> Tuple[List[Tuple[int,int,int,int]], List[float]]:
    # returns (rects, weights)
    rects, weights = HOG.detectMultiScale(
        img,
        winStride=(8, 8),
        padding=(8, 8),
        scale=1.05
    )
    rects_list = [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in rects]
    weights_list = [float(w) for w in weights] if weights is not None else []
    return rects_list, weights_list

def normalize_conf(w: float) -> float:
    # HOG weights are not probabilities; map to [0,1] smoothly.
    # This is a pragmatic confidence proxy for MVP experiments.
    return float(1.0 - np.exp(-max(0.0, w) / 2.5))

@APP.post("/infer", response_model=InferResponse)
def infer(req: InferRequest):
    t0 = time.perf_counter()

    try:
        img, t_pre = preprocess(req.image_b64, enable_face_blur=ENABLE_FACE_BLUR)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    t1 = time.perf_counter()
    rects, weights = detect_people(img)
    t_infer = (time.perf_counter() - t1) * 1000.0

    dets: List[Detection] = []
    for i, r in enumerate(rects):
        w = weights[i] if i < len(weights) else 0.0
        dets.append(Detection(label="person", bbox=list(r), confidence=normalize_conf(w)))

    md = req.metadata or {}
    sensor_id = str(md.get("sensor_id", "unknown"))
    ts = float(md.get("ts", time.time()))

    latency_ms = (time.perf_counter() - t0) * 1000.0
    return InferResponse(
        sensor_id=sensor_id,
        ts=ts,
        detections=dets,
        latency_ms=latency_ms,
        preprocess_ms=t_pre,
        infer_ms=t_infer,
    )

def main():
    import uvicorn
    host, port = INFER_ADDR.split(":")
    uvicorn.run("inference.app:APP", host=host, port=int(port), log_level="info")

if __name__ == "__main__":
    main()
