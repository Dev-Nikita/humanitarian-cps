import json
from pathlib import Path

rows = []

for p in Path("evaluation/reports").glob("report_*.json"):
    d = json.loads(p.read_text())
    rows.append({
        "scenario": d["scenario"],
        "loss": d["network"]["loss"],
        "delay_ms": d["network"]["delay_ms"],
        "jitter_ms": d["network"]["jitter_ms"],
        "mean_ms": round(d["metrics"]["mean_ms"], 1),
        "p95_ms": round(d["metrics"]["p95_ms"], 1),
        "reliability": round(d["metrics"]["reliability"], 2),
    })

rows = sorted(rows, key=lambda x: (x["scenario"], x["loss"], x["delay_ms"]))

print("| Scenario | Loss | Delay (ms) | Jitter (ms) | Mean (ms) | P95 (ms) | Reliability |")
print("|----------|------|------------|-------------|-----------|----------|-------------|")
for r in rows:
    print(
        f"| {r['scenario']} | {r['loss']} | {r['delay_ms']} | {r['jitter_ms']} | "
        f"{r['mean_ms']} | {r['p95_ms']} | {r['reliability']} |"
    )
