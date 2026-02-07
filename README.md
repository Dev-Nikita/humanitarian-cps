# humanitarian-cps (MVP, reproducible)

A minimal, working reference implementation for the paper sections (3–5):
- **edge**: preprocessing + CV inference (OpenCV HOG people detector; no model downloads)
- **orchestration**: confidence fusion + scenario runner
- **backend**: Go C2 API (events ingest + query + simple JWT auth)
- **simulation**: network degradation emulator + synthetic load generator + metrics
- **evaluation**: notebooks placeholder


---

## Quick start

### 1) Prerequisites
- Docker + Docker Compose

### 2) Run everything
```bash
docker compose up --build
```

Services:
- `c2-api` (Go): http://localhost:8080
- `edge-inference` (Python): http://localhost:8001
- `fusion` (Python): http://localhost:8002
- Postgres: localhost:5432 (db: `cps`, user/pass: `cps`/`cps`)

Health checks:
```bash
curl http://localhost:8080/healthz
curl http://localhost:8001/healthz
curl http://localhost:8002/healthz
```

---

## Run experiments (Scenario A/B/C)

The scenario runner is executed from a one-off container:
```bash
docker compose run --rm scenario-runner python -m orchestration.scenarios.run_scenario --scenario A
docker compose run --rm scenario-runner python -m orchestration.scenarios.run_scenario --scenario B --loss 0.2 --delay 120 --jitter 80
docker compose run --rm scenario-runner python -m orchestration.scenarios.run_scenario --scenario C --theta 0.6
```

It will:
1) generate synthetic frames
2) apply network degradation (optional)
3) call edge inference
4) call fusion
5) post events to C2 API
6) print metrics + write JSON report to `evaluation/reports/`

---

## API overview

### Edge inference
`POST /infer`
```json
{
  "image_b64": "<base64-encoded PNG/JPG>",
  "metadata": { "sensor_id": "cam-1", "ts": 1700000000.0 }
}
```
Returns detections:
```json
{
  "sensor_id": "cam-1",
  "ts": 1700000000.0,
  "detections": [{"label":"person","bbox":[x,y,w,h],"confidence":0.73}],
  "latency_ms": 43.2
}
```

### Fusion
`POST /fuse`
```json
{
  "results": [ ...edge outputs... ],
  "theta": 0.5
}
```

### C2 API
- `POST /events` (JWT optional)
- `GET /events?limit=50`
- `GET /healthz`

---

## Project layout
```
humanitarian-cps/
  edge/
  orchestration/
  backend/
  simulation/
  evaluation/
  docker-compose.yml
```

---

## Notes for the paper
- Section 3 uses latency budget decomposition; we measure and report P95.
- Section 5 uses reproducible simulation (loss/jitter/delay) + synthetic frames.

---

## License
MIT (see LICENSE)


## Optional: real datasets + AR/VR schema

- Dataset options and license-aware instructions: `docs/datasets.md`
- AR/VR event schema (JSON Schema): `schemas/arvr_event.schema.json`
- Examples: `schemas/examples/`

Scenario runner can use real images from a folder:
```bash
docker compose run --rm scenario-runner python -m orchestration.scenarios.run_scenario --scenario A --dataset data/coco/images/val2017 --n 50
```


## Kaggle presets (out of the box)

```bash
# Scenario A (People)
docker compose run --rm scenario-runner python -m orchestration.scenarios.run_scenario --scenario A --dataset data/kaggle/peoplecountingdataset --kaggle peoplecounting --n 50

# Scenario A (People, CCTV)
docker compose run --rm scenario-runner python -m orchestration.scenarios.run_scenario --scenario A --dataset data/kaggle/human-detection-dataset --kaggle cctv_human --n 50

# Scenario B (Fire)
docker compose run --rm scenario-runner python -m orchestration.scenarios.run_scenario --scenario B --dataset data/kaggle/fire-dataset --kaggle fire --loss 0.2 --delay 150 --jitter 80 --n 50

# Scenario B (FloodNet)
docker compose run --rm scenario-runner python -m orchestration.scenarios.run_scenario --scenario B --dataset data/kaggle/floodnet --kaggle floodnet --loss 0.1 --delay 200 --jitter 120 --n 50

# Scenario C (Damage 5-class)
docker compose run --rm scenario-runner python -m orchestration.scenarios.run_scenario --scenario C --dataset data/kaggle/disaster-damage-5class --kaggle damage5 --theta 0.7 --n 50
```
