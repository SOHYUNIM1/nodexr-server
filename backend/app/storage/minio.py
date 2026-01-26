from minio import Minio
from io import BytesIO
import uuid
import io
import logging
from datetime import timedelta
from app.core.config import settings
from pydantic import BaseModel
from uuid import UUID

logger = logging.getLogger(__name__)

# =================================================
# MinIO Client
# =================================================
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
)

# =================================================
# Bucket Initialization
# =================================================
def ensure_bucket() -> None:
    bucket_name = settings.MINIO_BUCKET
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
    except Exception as e:
        logger.error(f"MinIO ensure_bucket error: {e}")

# =================================================
# 이미지 업로드 및 처리 함수
# =================================================
def upload_generated_image(
    *,
    image_bytes: bytes,
    ext: str = "png",
) -> str:
    """Gemini 이미지 전용 업로드"""
    object_key = f"nodexr-assets/{uuid.uuid4()}.{ext}"

    upload_image_bytes(
        data=image_bytes,
        object_key=object_key,
        content_type=f"image/{ext}",
    )
    return f"minio:9000/{object_key}"

def upload_image_bytes(
    data: bytes,
    object_key: str,
    content_type: str,
):
    """버킷명과 파일명을 분리하여 MinIO에 저장"""
    bucket, object_name = object_key.split("/", 1)

    minio_client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )

def get_object_bytes(img_url: str) -> bytes:
    """URL에서 이미지 데이터를 읽어옴"""
    key = img_url.replace("minio:9000/", "")
    bucket, object_name = key.split("/", 1)

    resp = minio_client.get_object(bucket, object_name)
    data = resp.read()
    resp.close()
    resp.release_conn()
    return data

def generate_presigned_url(
    bucket: str,
    object_name: str,
    expires_sec: int = 60 * 60,
) -> str:
    return minio_client.presigned_get_object(
        bucket_name=bucket,
        object_name=object_name,
        expires=timedelta(seconds=expires_sec),
    )

class Generate3DRequest(BaseModel):
    room_id: UUID
    asset_id: UUID