.PHONY: install test lint validation docker-build k8s-demo

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -q

lint:
	python -m compileall packages scripts

validation:
	python scripts/run_validation.py --tenants examples/tenants.sample.json --output results/validation-report.html

k8s-demo:
	python scripts/render_k8s_jobs.py

docker-build:
	docker build -f docker/Dockerfile -t validation-platform:local .
