# app/utils/asset_url.py
import os

ASSET_BASE_URL = os.getenv("ASSET_BASE_URL", "").rstrip("/")

def build_asset_url(object_key: str | None) -> str | None:
    if not object_key:
        return None

    # 이미 완전한 URL이면 그대로 반환 (방어 코드)
    if object_key.startswith("http://") or object_key.startswith("https://"):
        return object_key

    # 실수로 minio:9000 이 붙은 경우 제거
    # ex) minio:9000/nodexr-assets/xxx.png
    if object_key.startswith("minio:9000/"):
        object_key = object_key.replace("minio:9000/", "", 1)

    # 실수로 /minio:9000/... 형태인 경우
    if object_key.startswith("/minio:9000/"):
        object_key = object_key.replace("/minio:9000/", "", 1)

    # 앞에 / 하나 정리
    object_key = object_key.lstrip("/")

    return f"{ASSET_BASE_URL}/{object_key}"