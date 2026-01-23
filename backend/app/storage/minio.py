from minio import Minio
from io import BytesIO
import uuid
from app.core.config import settings
from datetime import timedelta
import logging

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

    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

# app/storage/minio.py

from io import BytesIO
import uuid

def upload_generated_image(
    *,
    image_bytes: bytes,
    ext: str = "png",
) -> str:
    """
    Gemini 이미지 전용 업로드
    - object_key 자동 생성
    - content_type 자동 설정
    """
    object_key = f"nodexr-assets/{uuid.uuid4()}.{ext}"

    upload_image_bytes(
        data=image_bytes,
        object_key=object_key,
        content_type=f"image/{ext}",
    )

    return f"minio:9000/{object_key}"


# =================================================
# 이미지 업로드 함수
# =================================================
import io

def upload_image_bytes(
    data: bytes,
    object_key: str,
    content_type: str,
):
    """
    object_key 예:
      nodexr-assets/3d/xxx.glb
    """
    bucket, object_name = object_key.split("/", 1)

    minio_client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )



from urllib.parse import urlparse

def get_object_bytes(img_url: str) -> bytes:
    logger.info(f"[MINIO] get_object_bytes start: {img_url}")

    key = img_url.replace("minio:9000/", "")
    bucket, object_name = key.split("/", 1)

    logger.info(f"[MINIO] bucket={bucket}, object={object_name}")

    resp = minio_client.get_object(bucket, object_name)
    logger.info("[MINIO] get_object returned, start reading")

    data = resp.read()
    logger.info(f"[MINIO] read done, size={len(data)}")

    resp.close()
    resp.release_conn()
    return data



def generate_presigned_url(
    bucket: str,
    object_name: str,
    expires_sec: int = 60 * 60,  # 1시간
) -> str:
    """
    MinIO 객체에 대한 presigned GET URL 생성
    Unity / 외부 접근용
    """
    return minio_client.presigned_get_object(
        bucket_name=bucket,
        object_name=object_name,
        expires=timedelta(seconds=expires_sec),
    )
