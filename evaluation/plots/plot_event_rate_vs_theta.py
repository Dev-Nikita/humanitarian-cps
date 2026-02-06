import json
from pathlib import Path
import matplotlib.pyplot as plt

reports = Path("../reports").glob("report_C_*.json")

theta = []
rate = []

for r in reports:
    d = json.loads(r.read_text())
    theta.append(d["theta"])
    rate.append(d["metrics"]["n_ok"])  # or events/min if saved

plt.figure()
plt.plot(theta, rate, marker="o")
plt.xlabel("Confidence threshold θ")
plt.ylabel("Event rate (proxy)")
plt.tight_layout()
plt.savefig("figure9_event_rate_vs_theta.png", dpi=300)
plt.show()
