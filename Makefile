.PHONY: run-a run-b run-c run-all

run-a:
	docker compose run --rm scenario-runner \
	  python -m orchestration.scenarios.run_scenario \
	  --scenario A \
	  --dataset "data/kaggle/PeopleCountingDataSet" \
	  --kaggle peoplecounting \
	  --n 50

run-b:
	docker compose run --rm scenario-runner \
	  python -m orchestration.scenarios.run_scenario \
	  --scenario B \
	  --dataset "data/kaggle/Fire-Flood-Smoke-Landslide" \
	  --kaggle fire \
	  --loss 0.2 \
	  --delay 150 \
	  --jitter 80 \
	  --n 50

run-c:
	docker compose run --rm scenario-runner \
	  python -m orchestration.scenarios.run_scenario \
	  --scenario C \
	  --dataset "data/kaggle/Fire-Flood-Smoke-Landslide/disaster_dataset" \
	  --kaggle damage5 \
	  --theta 0.7 \
	  --n 50

run-all:
	$(MAKE) run-a
	$(MAKE) run-b
	$(MAKE) run-c
