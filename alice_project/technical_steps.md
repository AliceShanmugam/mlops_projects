# GUIDELINE : Technical steps A to Z

## Create project
    - use data csv file or script to download data
    - create data/raw folder and download or get data csv file here.

## Preprocess raw data
    - preprocess raw data file : clean remove stopwords etc., prepare for the model
    - create a script for this preprocessing in src/
    - save the preprocessed data in data/processed
    - save the vectorizer in models/

## Train data
    - train preprocessed data with the model
    - make predictions
    - evaluate score
    - save model (under condition)
    - create pipeline for production with model + vectorizer

## Launch preprocessing + train in container
    - create file run_pipeline.py to run steps preprocessing and train in the container
    - this file will be run when launching the container as mentionned in the dockerfile (CMD ["python", "src/run_pipeline.py"])

## Launch ml pipeline container
    - create Dockerfile and docker-compose to run pipeline in a container. Don't forget to mount volumes to get preprocessed data and model saved locally in data/processed/ or models/.
    - Run once to get data locally, if data change then rerun a container with same image (docker compose up), if script is changing, recreate a new image and run container (docker compose build)
    - No need to run everytime, if just need to explore API

## Launch API container
    - create src/api/main.py file to define api and endpoints
    - create src/api/model.py to load the model to use for predict endpoint
    - create src/api/schemas.py to define request and response type (json, int ...)
    - create Dockerfile.api (can also create a docker compose for api) to run api
    - Run to explore API

## Experiments with MLFlow
    - create a docker-compose file that manages all services Dockerfiles (one Dockerfile per service > microservices)
    - docker compose up --build (--build lorsque le Dockerfile est modifié)
    - Etudier difference entre runs/modifs des cripts/modifs des données ?