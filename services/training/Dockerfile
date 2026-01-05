
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY train_linearsvm.py .
COPY train_cnn.py .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
