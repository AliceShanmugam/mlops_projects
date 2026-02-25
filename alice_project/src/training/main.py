from fastapi import FastAPI
import subprocess

app = FastAPI()

@app.post("/train")
def trigger_training():
    result = subprocess.run(
        ["python", "train.py"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {"status": "error", "details": result.stderr}

    return {"status": "success"}