from minio import Minio
from io import BytesIO
import uuid
from app.core.config import settings

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

# =================================================
# 이미지 업로드 함수
# =================================================
def upload_image_bytes(img_byte_array: BytesIO) -> str:
    """
    이미지를 MinIO에 업로드하고, MinIO URL을 반환하는 함수
    :param img_byte_array: 업로드할 이미지 (이미지 byte 배열)
    :return: MinIO에서 반환된 이미지 URL
    """
    # 고유한 객체 이름 생성
    file_name = f"{uuid.uuid4()}.png"
    bucket_name = settings.MINIO_BUCKET

    try:
        # MinIO에 이미지 업로드
        minio_client.put_object(bucket_name, file_name, img_byte_array, len(img_byte_array.getvalue()))
        # MinIO에서 이미지 URL 반환
        img_url = f"{settings.MINIO_ENDPOINT}/{bucket_name}/{file_name}"
        return img_url
    except Exception as err:
        print(f"Error uploading image to MinIO: {err}")
        return ""