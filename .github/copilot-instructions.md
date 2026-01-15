# GitHub Copilot Instructions for MLOps Project

## Architecture Overview
**Multimodal Classification Pipeline** (Rakuten Challenge): Classifies products by text (SVM + TF-IDF) and images (CNN PyTorch) via microservices. Four containerized services communicate within `mlops_network` Docker bridge network:
- **gateway** (port 8000): OAuth2 auth layer; routes /train/* (admin) and /predict/* (user) to backend
- **training** (port 8002): FastAPI endpoints POST /train/svm, /train/cnn using background tasks; logs to MLflow
- **inference** (port 8001): Loads joblib (SVM/TF-IDF) + PyTorch CNN models; serves predictions
- **mlflow** (port 5000): Centralized experiment tracking; all runs logged with params/metrics/artifacts

## Critical Data & Model Paths
**Data flow**: `data/raw/` (CSV + image_train/) → `src/preprocessing/` → `data/processed/train_clean.csv` (labelized). Models pickled to `models/{text,images}/`: SVM+TF-IDF in `.joblib`, CNN in `.pt`. Container paths: `/app/data`, `/app/src`, `/app/models` (all mounted as volumes in docker-compose.yml).

## Build & Deploy Workflow
1. **Local dev**: `docker-compose build --no-cache && docker-compose up -d` (rebuilds all services)
2. **Production**: Use `deploiement.ps1` (PowerShell): cleans containers/volumes, rebuilds images, starts services, tails inference logs
3. **Health checks**: All services expose `/health` GET endpoints; gateway uses these to route requests
4. **Model availability**: Inference service gracefully handles missing MLflow registry—loads models from `models/` directory as fallback

## Key Implementation Patterns

### Model Training (src/training/ & src/train_models/)
- **Entry points**: `run_training_text.py` calls `train_linearsvm.py`; `run_training_images.py` calls `train_cnn.py`
- **MLflow context**: Training service wraps pipelines in `mlflow.start_run(run_name=...)` with logged params
- **SVM path**: Tokenize (src/preprocessing/) → TF-IDF vectorizer (sklearn) → LinearSVM; both saved as single joblib files
- **CNN architecture**: SimpleCNN class (8 output classes) in `src/train_models/train_cnn.py`; PyTorch .pt weights loaded in inference
- **Shared params**: NUM_CLASSES=8, IMAGE_SIZE=128px; label_name mapping from `data/processed/train_clean.csv`

### Model Inference (api/main.py & src/inference/main.py)
- **Dual-path**: Accept text → TF-IDF vectorize → SVM predict; image → PIL resize + normalize → CNN predict
- **Label resolution**: Load `train_clean.csv`, build `LABEL_ID_TO_NAME` dict, return label name (not ID)
- **Device handling**: CNN runs on CPU (DEVICE=torch.device("cpu")); no GPU in current setup
- **Model persistence**: On gateway health-check failure, inference returns cached predictions (graceful degradation)

### Authentication & Authorization (src/gateway/)
- **OAuth2 scheme**: create_access_token() generates JWT; Depends(require_admin) / Depends(require_user) decorators
- **Role-based routes**: POST /train/* requires admin; POST /predict/* requires user role
- **Service discovery**: Environment vars INFERENCE_URL, TRAINING_URL (docker-compose passes via env)

## Testing & Validation
- **pytest scope**: `tests/test_*.py` only; config in `pytest.ini` (testpaths=tests)
- **Coverage by module**:
  - `test_read_data.py`: CSV loading, shape validation
  - `test_preprocessing.py`: Text cleaning (BeautifulSoup, langdetect)
  - `test_features.py`: TF-IDF vectorizer fit/transform
  - `test_model_training2.py`: SVM + CNN training, artifact generation
  - `test_api.py`: FastAPI endpoint mocking (text + image inputs)
- **Run tests**: `pytest` (auto-discovers tests/test_*.py)

## Common Modifications
- **Add new label class**: Update NUM_CLASSES in CNN + retrain; regenerate `train_clean.csv`
- **Change image size**: Update IMAGE_SIZE (128) consistently in `train_cnn.py` and inference models
- **Add preprocessing step**: Insert in `src/preprocessing/`, call from training pipelines before vectorization
- **Extend gateway routes**: Mirror pattern in `gateway/main.py`: define Depends(), call service_url via requests.post()

## Troubleshooting & Known Issues
- **Inference fails to load models at startup**: Ensure `docker-compose.yml` has `- ./models:/app/models` volume mounts for both inference and training services. Without this, models trained in one container can't be accessed in another. Service gracefully degrades if models missing—logs warnings but continues running.
- **500 errors on predict endpoints**: If inference service started but models missing, you'll get HTTP 503 "Service Unavailable" with descriptive message. Train models first via `POST /train/svm` and `POST /train/cnn` endpoints (requires admin auth), then models auto-save to `models/{text,images}/` for inference to load.
- **MLflow not ready when inference starts**: Expected in fresh deployments. Inference prefers loading from local files (`models/` directory) over MLflow registry—graceful fallback ensures service stays up.
- **"Image not found" on predict**: Image paths are relative to `data/raw/image_train/`; pass only filename (e.g., `"image_528113_product_923222.jpg"`).
- **TF-IDF transform mismatch**: If retrain SVM, ensure same corpus—TF-IDF vocabulary must match between training and inference. Both saved in `models/text/` together.

## Dependencies & Versions
Core stack: FastAPI, PyTorch, scikit-learn, MLflow 2.9.2, pandas, joblib. See `requirements.txt` and service-specific `src/{training,inference,gateway}/requirements.txt`. Build context is project root (Dockerfiles use relative paths like `src/training/Dockerfile`).