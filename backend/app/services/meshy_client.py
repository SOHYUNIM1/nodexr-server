# app/services/meshy_client.py

import os
import time
import base64
import logging
import mimetypes
import uuid
import requests
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.asset import Asset
from app.storage.minio import get_object_bytes, upload_image_bytes

logger = logging.getLogger(__name__)

# =========================================================
# Config
# =========================================================
MESHY_API_KEY = os.getenv("MESHY_API_KEY")
BASE_URL = "https://api.meshy.ai/openapi/v1"
ASSET_BASE_URL = os.getenv("ASSET_BASE_URL", "http://localhost:9000")

HEADERS = {
    "Authorization": f"Bearer {MESHY_API_KEY}",
    "Content-Type": "application/json",
}

SUPPORTED_MIME = {"image/png", "image/jpeg"}


# =========================================================
# Internal utils
# =========================================================
def _build_plain_url(object_key: str) -> str:
    return f"{ASSET_BASE_URL.rstrip('/')}/{object_key}"


# =========================================================
# MinIO → Data URI (Meshy input)
# =========================================================
def _minio_image_to_data_uri(
    img_url: str,
    max_bytes: int = 8 * 1024 * 1024,
) -> str:
    logger.info("[MESHY][STEP 1] Load image from MinIO")
    logger.info(f"[MESHY][STEP 1] img_url={img_url}")

    data = get_object_bytes(img_url)
    size = len(data)
    logger.info(f"[MESHY][STEP 1] Image bytes loaded (size={size})")

    if size > max_bytes:
        logger.error("[MESHY][STEP 1] Image too large")
        raise ValueError(f"Image too large for Meshy: {size} bytes")

    mime, _ = mimetypes.guess_type(img_url)
    logger.info(f"[MESHY][STEP 1] Detected mime={mime}")

    if mime not in SUPPORTED_MIME:
        logger.error("[MESHY][STEP 1] Unsupported mime type")
        raise ValueError(f"Unsupported image mime type: {mime}")

    encoded = base64.b64encode(data).decode("utf-8")
    logger.info("[MESHY][STEP 1] Image encoded to base64")

    return f"data:{mime};base64,{encoded}"


# =========================================================
# Meshy API
# =========================================================
def _create_image_to_3d_task(image_data_uri: str) -> str:
    logger.info("[MESHY][STEP 2] Create image-to-3d task (request start)")
    logger.info(f"[MESHY][STEP 2] Payload size={len(image_data_uri)}")
    
    payload = {
        "image_url": image_data_uri,
        "should_texture": False,
        "enable_pbr": False,
        "should_remesh": False,
    }


    #payload = {
    #    "image_url": image_data_uri,
    #    "should_texture": True,
    #    "enable_pbr": True,
    #    "should_remesh": True,
    #    "save_pre_remeshed_model": True,
    #}

    try:
        res = requests.post(
            f"{BASE_URL}/image-to-3d",
            headers=HEADERS,
            json=payload,
            timeout=30,
        )
    except Exception as e:
        logger.exception("[MESHY][STEP 2] Request failed")
        raise

    logger.info(
        f"[MESHY][STEP 2] Response received status={res.status_code}"
    )

    if res.status_code not in (200, 202):
        logger.error(f"[MESHY][STEP 2] Body={res.text}")
        res.raise_for_status()

    task_id = res.json().get("result")
    logger.info(f"[MESHY][STEP 2] Task accepted task_id={task_id}")

    return task_id


def _poll_image_to_3d_task(
    task_id: str,
    poll_interval: int = 5,
    timeout_sec: int = 600,
) -> str:
    logger.info(f"[MESHY][STEP 3] Start polling task_id={task_id}")

    deadline = time.time() + timeout_sec
    attempt = 0

    while time.time() < deadline:
        attempt += 1
        logger.info(f"[MESHY][STEP 3] Poll attempt #{attempt}")

        try:
            res = requests.get(
                f"{BASE_URL}/image-to-3d/{task_id}",
                headers=HEADERS,
                timeout=20,
            )
        except Exception:
            logger.exception("[MESHY][STEP 3] Poll request failed")
            raise

        logger.info(
            f"[MESHY][STEP 3] Poll response status={res.status_code}"
        )

        if res.status_code != 200:
            logger.error(f"[MESHY][STEP 3] Body={res.text}")
            res.raise_for_status()

        data = res.json()
        status = data.get("status")
        logger.info(f"[MESHY][STEP 3] status={status}")

        if status == "SUCCEEDED":
            glb_url = data.get("model_urls", {}).get("glb")
            logger.info(f"[MESHY][STEP 3] SUCCEEDED glb_url={glb_url}")

            if not glb_url:
                raise RuntimeError("Meshy SUCCEEDED but glb url missing")
            return glb_url

        if status == "FAILED":
            err = (data.get("task_error") or {}).get("message", "")
            logger.error(f"[MESHY][STEP 3] FAILED err={err}")
            raise RuntimeError(f"Meshy task failed: {err}")

        time.sleep(poll_interval)

    logger.error("[MESHY][STEP 3] Polling timeout")
    raise TimeoutError("Meshy image-to-3d task timed out")


# =========================================================
# Public API
# =========================================================
def generate_3d(asset_id: UUID, db: Session) -> str:
    logger.info(f"[MESHY][START] generate_3d asset_id={asset_id}")

    # 1️⃣ asset 조회
    asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
    if not asset:
        logger.error("[MESHY] Asset not found")
        raise ValueError("Asset not found")

    img_url = asset.img_url
    logger.info(f"[MESHY] Source img_url={img_url}")

    # 2️⃣ Meshy input
    image_data_uri = _minio_image_to_data_uri(img_url)

    # 3️⃣ Meshy 실행
    task_id = _create_image_to_3d_task(image_data_uri)
    meshy_glb_url = _poll_image_to_3d_task(task_id)

    # 4️⃣ Meshy 결과 다운로드
    logger.info(f"[MESHY][STEP 4] Download GLB from {meshy_glb_url}")
    glb_res = requests.get(meshy_glb_url, timeout=60)
    glb_res.raise_for_status()
    glb_bytes = glb_res.content
    logger.info(f"[MESHY][STEP 4] GLB downloaded size={len(glb_bytes)}")

    # 5️⃣ MinIO 업로드
    object_key = f"nodexr-assets/3d/{uuid.uuid4()}.glb"
    logger.info(f"[MESHY][STEP 5] Upload GLB to MinIO object_key={object_key}")

    upload_image_bytes(
        data=glb_bytes,
        object_key=object_key,
        content_type="model/gltf-binary",
    )

    # 6️⃣ Unity용 plain URL
    plain_url = _build_plain_url(object_key)
    logger.info(f"[MESHY][END] 3D asset ready plain_url={plain_url}")

    return plain_url