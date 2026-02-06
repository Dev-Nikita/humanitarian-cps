import argparse
import json
import os
import time
import statistics
from pathlib import Path
from typing import List

from simulation.network.emulator import NetworkEmulator, NetworkProfile
from simulation.load.generate_frames import synthetic_frames
from simulation.load.dataset_adapter import frames_from_folder
from simulation.load.kaggle_adapter import (
    kaggle_peoplecounting_frames,
    kaggle_human_detection_cctv_frames,
    kaggle_fire_dataset_frames,
    kaggle_floodnet_frames,
    kaggle_disaster_damage_5class_frames,
)
from simulation.metrics.metrics import compute

EDGE_URL = os.getenv("EDGE_URL", "http://localhost:8001").rstrip("/")
FUSION_URL = os.getenv("FUSION_URL", "http://localhost:8002").rstrip("/")
C2_URL = os.getenv("C2_URL", "http://localhost:8080").rstrip("/")


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


def post_event(em: NetworkEmulator, event: dict) -> None:
    r = em.post_json(f"{C2_URL}/events", event, timeout=10.0)
    r.raise_for_status()


from pathlib import Path
import json

def write_preview_files(preview_events, metrics):
    preview_dir = Path("/app/evaluation/preview")
    preview_dir.mkdir(parents=True, exist_ok=True)

    # --- scenario-aware naming ---
    sc = metrics.get("scenario", "X")

    # ===== EVENTS (per-scenario) =====
    events_path = preview_dir / f"events_{sc}.json"
    if preview_events:
        events_path.write_text(
            json.dumps(preview_events[-50:], indent=2),
            encoding="utf-8",
        )

    # ===== METRICS (per-scenario) =====
    (preview_dir / f"metrics_{sc}.json").write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )

    # ===== METRICS HISTORY (per-scenario) =====
    hist_path = preview_dir / f"metrics_history_{sc}.json"
    history = json.loads(hist_path.read_text()) if hist_path.exists() else []
    history.append(metrics)

    hist_path.write_text(
        json.dumps(history[-200:], indent=2),
        encoding="utf-8",
    )

    # ===== LATEST POINTERS (used by index.html) =====
    # metrics.json — всегда перезаписываем
    (preview_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )

    # events.json — ТОЛЬКО если есть события
    if preview_events:
        (preview_dir / "events.json").write_text(
            json.dumps(preview_events[-50:], indent=2),
            encoding="utf-8",
        )
        (preview_dir / "events_latest.json").write_text(
            json.dumps(preview_events[-50:], indent=2),
            encoding="utf-8",
        )



def select_frames(args) :
    """
    Returns an iterator of (img_b64, meta) depending on --kaggle / --dataset.
    """
    n = args.n

    if args.kaggle == "peoplecounting":
        return kaggle_peoplecounting_frames(args.dataset, max_n=n)

    if args.kaggle == "cctv_human":
        return kaggle_human_detection_cctv_frames(args.dataset, max_n=n)

    if args.kaggle == "fire":
        return kaggle_fire_dataset_frames(args.dataset, max_n=n)

    if args.kaggle == "floodnet":
        return kaggle_floodnet_frames(args.dataset, max_n=n)

    if args.kaggle == "damage5":
        return kaggle_disaster_damage_5class_frames(args.dataset, max_n=n)

    # Generic: any folder with images (recursive adapter)
    if args.dataset:
        return frames_from_folder(args.dataset, sensor_id="cam-1", max_n=n)

    # Fallback: synthetic stream
    return synthetic_frames("cam-1", n=n)


def run(args) -> None:
    scenario = args.scenario
    loss = args.loss
    delay = args.delay
    jitter = args.jitter
    theta = args.theta
    n = args.n

    em = NetworkEmulator(
        NetworkProfile(loss=loss, delay_ms=delay, jitter_ms=jitter)
    )

    ok_lat_total: List[float] = []
    n_sent = 0

    # ---- Live metrics state ----
    latencies: List[float] = []
    events = 0
    t_start = time.time()

    # ---- For HTML preview ----
    preview_events: List[dict] = []

    frame_iter = select_frames(args)

    for img_b64, meta in frame_iter:
        n_sent += 1
        t0 = time.perf_counter()

        try:
            # ---- Edge inference ----
            ir = em.post_json(
                f"{EDGE_URL}/infer",
                {
                    "image_b64": img_b64,
                    "metadata": {
                        "sensor_id": getattr(meta, "sensor_id", "cam-1"),
                        "ts": getattr(meta, "ts", time.time()),
                    },
                },
                timeout=10.0,
            )
            ir.raise_for_status()
            edge_out = ir.json()

            # ---- Fusion ----
            fr = em.post_json(
                f"{FUSION_URL}/fuse",
                {
                    "results": [edge_out],
                    "theta": theta,
                },
                timeout=10.0,
            )
            fr.raise_for_status()
            fused = fr.json()

            # ---- Events ----
            for ev in fused.get("events", []):
                post_event(em, ev)
                events += 1
                preview_events.append(ev)

            # ---- Latency ----
            total_ms = (time.perf_counter() - t0) * 1000.0
            ok_lat_total.append(total_ms)
            latencies.append(total_ms)

            # ---- Live console metrics ----
            if len(latencies) % 10 == 0:
                if len(latencies) >= 20:
                    p95 = statistics.quantiles(latencies, n=20)[18]
                else:
                    p95 = max(latencies)

                rate = (
                    events / (time.time() - t_start) * 60
                    if (time.time() - t_start) > 0
                    else 0.0
                )

                print(
                    f"[LIVE] frames={len(latencies)} | "
                    f"P95={p95:.1f} ms | "
                    f"events/min={rate:.1f}"
                )

                # ---- Live HTML metrics update ----
                preview_metrics = {
                    "scenario": scenario,
                    "dataset": args.dataset,
                    "kaggle": args.kaggle,
                    "p95_latency_ms": p95,
                    "mean_latency_ms": sum(latencies) / len(latencies),
                    "events_per_min": rate,
                    "n_frames": len(latencies),
                    "timestamp": now_iso(),
                }

                write_preview_files(preview_events, preview_metrics)

        except Exception:
            # simulated packet loss or runtime error
            pass

    # ---- Final aggregated report ----
    m = compute(n_sent, ok_lat_total)

    report = {
        "scenario": scenario,
        "time_utc": now_iso(),
        "dataset": args.dataset,
        "kaggle": args.kaggle,
        "network": {
            "loss": loss,
            "delay_ms": delay,
            "jitter_ms": jitter,
        },
        "theta": theta,
        "metrics": {
            "n_sent": m.n_sent,
            "n_ok": m.n_ok,
            "reliability": m.reliability,
            "p50_ms": m.p50_ms,
            "p95_ms": m.p95_ms,
            "mean_ms": m.mean_ms,
        },
    }

    outdir = Path("/app/evaluation/reports")
    outdir.mkdir(parents=True, exist_ok=True)
    outpath = outdir / f"report_{scenario}_{int(time.time())}.json"
    outpath.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # ---- Final preview metrics (last snapshot) ----
    if latencies:
        p95_live = (
            statistics.quantiles(latencies, n=20)[18]
            if len(latencies) >= 20
            else max(latencies)
        )
        mean_live = sum(latencies) / len(latencies)
        rate_live = events / (time.time() - t_start) * 60
    else:
        p95_live = mean_live = rate_live = 0.0

    final_preview_metrics = {
        "scenario": scenario,
        "dataset": args.dataset,
        "kaggle": args.kaggle,
        "p95_latency_ms": p95_live,
        "mean_latency_ms": mean_live,
        "events_per_min": rate_live,
        "n_frames": len(latencies),
        "timestamp": now_iso(),
    }

    write_preview_files(preview_events, final_preview_metrics)

    print(json.dumps(report, indent=2))
    print(f"Report saved to: {outpath}")
    print("Preview files saved to: /app/evaluation/preview/{events.json, metrics.json}")



def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", choices=["A", "B", "C"], default="A")
    ap.add_argument("--loss", type=float, default=0.0)
    ap.add_argument("--delay", type=float, default=0.0)
    ap.add_argument("--jitter", type=float, default=0.0)
    ap.add_argument("--theta", type=float, default=0.5)
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--dataset", type=str, default="", help="Path to folder of images to use instead of synthetic frames")
    ap.add_argument(
        "--kaggle",
        choices=["peoplecounting", "cctv_human", "fire", "floodnet", "damage5", ""],
        default="",
        help="Kaggle dataset preset (controls dataset adapter). Empty = generic folder/synthetic.",
    )

    args = ap.parse_args()

    # scenario defaults
    if args.scenario == "B":
        if args.loss == 0.0 and args.delay == 0.0 and args.jitter == 0.0:
            args.loss, args.delay, args.jitter = 0.15, 120.0, 80.0
    elif args.scenario == "C":
        if args.theta == 0.5:
            args.theta = 0.7

    run(args)


if __name__ == "__main__":
    main()
