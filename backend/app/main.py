from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from app.storage.minio import ensure_bucket
from app.api.rooms import router as room_router
from app.api.ws import router as ws_router
from app.api.utterances import router as utter_router
from app.api.select_2d import router as select_2d_router
from app.api.category import router as category_router
from app.api.generate_3d import router as generate_3d_router

# ===============================
# FastAPI App
# ===============================

app = FastAPI(
    title="NodeXR API",
    description="NodeXR Semantic Graph & Image Generation API",
    version="0.1.0",
)

# ===============================
# CORS
# ===============================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 단계
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    ensure_bucket()


app.include_router(room_router)
app.include_router(ws_router)
app.include_router(utter_router)
app.include_router(select_2d_router)
app.include_router(category_router)
app.include_router(generate_3d_router)