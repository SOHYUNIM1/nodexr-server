from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import httpx
import logging

from app.storage.minio import ensure_bucket
from app.api.rooms import router as room_router
from app.api.ws import router as ws_router
from app.api.utterances import router as utter_router
from app.api.select_2d import router as select_2d_router
from app.api.category import router as category_router
from app.api.generate_3d import router as generate_3d_router

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NodeXR API",
    description="NodeXR Semantic Graph & Image Generation API",
    version="0.1.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =================================================
# 이미지 서빙 프록시 (Docker 환경용 최종 수정)
# =================================================
@app.get("/nodexr-assets/{file_path:path}")
async def proxy_minio(file_path: str):
    """
    유니티의 요청을 받아 MinIO 컨테이너(9000번 포트)에서 이미지를 가져옵니다.
    """
    # Docker 네트워크 내부 주소인 'minio'를 사용합니다.
    base_minio_url = "http://minio:9000" 
    target_url = f"{base_minio_url}/nodexr-assets/{file_path}"
    
    logger.info(f"🔍 Proxy Request to: {target_url}")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(target_url, timeout=10.0)
            
            if resp.status_code != 200:
                logger.error(f"❌ MinIO Error: {resp.status_code} for {target_url}")
                return {"error": "File not found in MinIO"}, 404
            
            return StreamingResponse(
                resp.iter_bytes(), 
                media_type=resp.headers.get("content-type", "image/png")
            )
        except Exception as e:
            logger.error(f"🔥 Proxy Connection Failed: {str(e)}")
            return {"error": "MinIO server unreachable"}, 500

@app.on_event("startup")
def startup():
    ensure_bucket()

# Router 등록
app.include_router(room_router)
app.include_router(ws_router)
app.include_router(utter_router)
app.include_router(select_2d_router)
app.include_router(category_router)
app.include_router(generate_3d_router)