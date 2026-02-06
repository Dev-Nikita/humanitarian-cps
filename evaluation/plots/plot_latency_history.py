import json
import matplotlib.pyplot as plt

with open("../preview/metrics_history.json") as f:
    hist = json.load(f)

p95 = [m["p95_latency_ms"] for m in hist]

plt.figure()
plt.plot(p95)
plt.xlabel("Time (updates)")
plt.ylabel("P95 latency (ms)")
plt.title("Latency P95 history")
plt.tight_layout()
plt.savefig("figure8_latency_history.png", dpi=300)
plt.show()
