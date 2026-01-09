from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    rooms,
    utterances,
    graph,
    generate_2d,
    generate_3d,
)

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

# ===============================
# Routers
# ===============================

# 방 생성
#app.include_router(
#    rooms.router,
#    prefix="/rooms",
#    tags=["Rooms"],
#)

# 발화 (STT 종료)
app.include_router(
    utterances.router,
    prefix="/utterances",
    tags=["Utterances"],
)

# 그래프
app.include_router(
    graph.router,
    prefix="/graph",
    tags=["Graph"],
)

# 2D 이미지 생성
#app.include_router(
#    generate_2d.router,
#    prefix="/2d",
#    tags=["2D Generation"],
#)

# 3D 이미지 생성
#app.include_router(
#    generate_3d.router,
#    prefix="/3d",
#    tags=["3D Generation"],
#)

# ===============================
# Health Check
# ===============================

@app.get("/")
async def root():
    return {"status": "NodeXR backend alive"}