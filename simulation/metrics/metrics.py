from dataclasses import dataclass, asdict
from typing import List, Dict
import numpy as np

@dataclass
class Metrics:
    n_sent: int
    n_ok: int
    p50_ms: float
    p95_ms: float
    mean_ms: float
    reliability: float

def latency_stats(lat_ms: List[float]) -> Dict[str, float]:
    if not lat_ms:
        return {"p50": 0.0, "p95": 0.0, "mean": 0.0}
    arr = np.array(lat_ms, dtype=float)
    return {
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
        "mean": float(np.mean(arr)),
    }

def compute(n_sent: int, ok_lat_ms: List[float]) -> Metrics:
    stats = latency_stats(ok_lat_ms)
    n_ok = len(ok_lat_ms)
    reliability = (n_ok / n_sent) if n_sent > 0 else 0.0
    return Metrics(
        n_sent=n_sent,
        n_ok=n_ok,
        p50_ms=stats["p50"],
        p95_ms=stats["p95"],
        mean_ms=stats["mean"],
        reliability=reliability,
    )
