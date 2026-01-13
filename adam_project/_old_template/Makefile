deploy:
	prefect deploy flows/test_local_deployment.py:hello_flow \
    	--name hello-deployment \
    	--pool default-agent-pool \
    	--work-queue default

run:
	prefect deployment run 'Hello Flow/hello-deployment'

quicky:
	python flows/test_flow.py