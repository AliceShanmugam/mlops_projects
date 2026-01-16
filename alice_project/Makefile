build:
	docker build -t ml-pipeline .

run:
	docker run --rm \
	-v $(PWD)/data:/app/data \
	-v $(PWD)/models:/app/models \
	ml-pipeline