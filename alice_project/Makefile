install:
	pip install -r requirements.txt

test:
	pytest tests/

run-api:
	uvicorn api.main:app --host 0.0.0.0 --port 8000

build:
	docker build -t ml-api .

docker-run:
	docker run -p 8000:8000 ml-api