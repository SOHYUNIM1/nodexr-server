from minio import Minio
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