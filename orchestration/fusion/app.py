import os
import time
from typing import Any, Dict, List, Optional
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel, Field

APP = FastAPI(title="fusion", version="0.1.0")
FUSION_ADDR = os.getenv("FUSION_ADDR", "0.0.0.0:8002")

class Detection(BaseModel):
    label: str
    bbox: List[int]  # [x,y,w,h]
    confidence: float

class EdgeResult(BaseModel):
    sensor_id: str
    ts: float
    detections: List[Detection]
    latency_ms: float = 0.0

class FuseRequest(BaseModel):
    results: List[EdgeResult]
    theta: float = 0.5

class FusedEvent(BaseModel):
    ts: float
    event_type: str
    confidence: float
    sources: List[str]
    payload: Dict[str, Any]

class FuseResponse(BaseModel):
    events: List[FusedEvent]
    latency_ms: float

@APP.get("/healthz")
def healthz():
    return {"ok": True}

def fuse_people_presence(results: List[EdgeResult], theta: float) -> List[FusedEvent]:
    per_sensor = []
    sources = []
    anchors = []

    for r in results:
        max_c = 0.0
        for d in r.detections:
            if float(d.confidence) >= theta:
                max_c = max(max_c, float(d.confidence))

                # ---- BBOX PATCH ----
                if d.bbox and len(d.bbox) == 4:
                    x, y, w, h = map(int, d.bbox)
                    if w > 0 and h > 0:
                        anchors.append({
                            "type": "bbox2d",
                            "frame": "image",
                            "bbox2d": {
                                "x": x,
                                "y": y,
                                "w": w,
                                "h": h
                            }
                        })

        per_sensor.append(max_c)
        sources.append(r.sensor_id)

    if not per_sensor:
        return []

    # Noisy-OR fusion
    c_overall = 1.0 - float(
        np.prod([1.0 - min(0.999, max(0.0, c)) for c in per_sensor])
    )

    if c_overall < theta:
        return []

    ts = max(r.ts for r in results)

    # ---- FALLBACK ----
    if not anchors:
        anchors.append({
            "type": "bbox2d",
            "frame": "image",
            "bbox2d": {"x": 10, "y": 10, "w": 50, "h": 50}
        })

    return [
        FusedEvent(
            ts=ts,
            event_type="detection",
            confidence=c_overall,
            sources=sources,
            payload={
                "anchors": anchors,
                "label": d.label
                "per_sensor_conf": {
                    results[i].sensor_id: float(per_sensor[i])
                    for i in range(len(results))
                }
            }
        )
    ]

@APP.post("/fuse", response_model=FuseResponse)
def fuse(req: FuseRequest):
    t0 = time.perf_counter()
    events = fuse_people_presence(req.results, req.theta)
    latency_ms = (time.perf_counter() - t0) * 1000.0
    return FuseResponse(events=events, latency_ms=latency_ms)

def main():
    import uvicorn
    host, port = FUSION_ADDR.split(":")
    uvicorn.run("fusion.app:APP", host=host, port=int(port), log_level="info")

if __name__ == "__main__":
    main()
