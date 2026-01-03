from fastapi import FastAPI
from app.storage.minio import ensure_bucket

app = FastAPI()

@app.on_event("startup")
def startup():
    ensure_bucket()

@app.get("/")
def ping():
    return {"status": "XR backend alive"}