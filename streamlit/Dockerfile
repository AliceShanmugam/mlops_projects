FROM python:3.12-slim

WORKDIR /app

COPY streamlit/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["streamlit", "run", "streamlit_rakuten.py", "--host", "0.0.0.0", "--port", "8501"]
