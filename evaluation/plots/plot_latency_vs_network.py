import json
from pathlib import Path
import matplotlib.pyplot as plt

reports = Path("../reports").glob("report_*.json")

profiles = []
p95 = []

for r in reports:
    data = json.loads(r.read_text())
    net = data["network"]
    label = f"loss={net['loss']}, d={net['delay_ms']}, j={net['jitter_ms']}"
    profiles.append(label)
    p95.append(data["metrics"]["p95_ms"])

plt.figure()
plt.plot(profiles, p95, marker="o")
plt.xticks(rotation=30, ha="right")
plt.ylabel("P95 latency (ms)")
plt.xlabel("Network profile")
plt.tight_layout()
plt.savefig("figure6_latency_vs_network.png", dpi=300)
plt.show()
