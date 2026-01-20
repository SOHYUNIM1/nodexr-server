# app/services/meshy_service.py

import os
import time
import base64
import logging
import mimetypes
import requests

from app.storage.minio import get_object_bytes

logger = logging.getLogger(__name__)

# =========================================================
# Meshy API Config
# =========================================================
MESHY_API_KEY = os.getenv("MESHY_API_KEY")
BASE_URL = "https://api.meshy.ai/openapi/v1"

HEADERS = {
    "Authorization": f"Bearer {MESHY_API_KEY}",
    "Content-Type": "application/json",
}

SUPPORTED_MIME = {"image/png", "image/jpeg"}  # Meshy 허용 포맷


# =========================================================
# Internal: MinIO → Data URI
# =========================================================
def _minio_image_to_data_uri(
    img_url: str,
    max_bytes: int = 8 * 1024 * 1024,
) -> str:
    logger.info("[MESHY][STEP 1] Load image from MinIO")

    data = get_object_bytes(img_url)
    size = len(data)

    logger.info(f"[MESHY][STEP 1] Image loaded (size={size} bytes)")

    if size > max_bytes:
        raise ValueError(f"Image too large for Meshy: {size} bytes")

    mime, _ = mimetypes.guess_type(img_url)
    logger.info(f"[MESHY][STEP 1] Detected mime type: {mime}")

    if mime not in SUPPORTED_MIME:
        raise ValueError(f"Unsupported image mime type: {mime}")

    encoded = base64.b64encode(data).decode("utf-8")
    logger.info("[MESHY][STEP 1] Converted image to data URI")

    return f"data:{mime};base64,{encoded}"


# =========================================================
# Meshy API Calls
# =========================================================
def _create_image_to_3d_task(image_url_or_data_uri: str) -> str:
    logger.info("[MESHY][STEP 2] Create image-to-3d task")

    payload = {
        "image_url": image_url_or_data_uri,
        "should_texture": True,
        "enable_pbr": True,
        "should_remesh": True,
        "save_pre_remeshed_model": True,
    }

    res = requests.post(
        f"{BASE_URL}/image-to-3d",
        headers=HEADERS,
        json=payload,
        timeout=30,
    )

    logger.info(
        f"[MESHY][STEP 2] Task create response: "
        f"status={res.status_code}, body={res.text}"
    )

    # Meshy는 비동기 접수면 202 가능
    if res.status_code not in (200, 202):
        logger.error("[MESHY][STEP 2] Task creation failed")
        res.raise_for_status()

    task_id = res.json()["result"]
    logger.info(f"[MESHY][STEP 2] Task accepted (task_id={task_id})")

    return task_id


def _poll_image_to_3d_task(
    task_id: str,
    poll_interval: int = 5,
    timeout_sec: int = 600,  # ⬅️ 10분 권장
) -> str:
    logger.info(f"[MESHY][STEP 3] Start polling (task_id={task_id})")

    deadline = time.time() + timeout_sec
    attempt = 0

    while time.time() < deadline:
        attempt += 1

        res = requests.get(
            f"{BASE_URL}/image-to-3d/{task_id}",
            headers=HEADERS,
            timeout=20,
        )

        if res.status_code != 200:
            logger.error(
                f"[MESHY][STEP 3] Poll failed "
                f"(status={res.status_code}, body={res.text})"
            )
            res.raise_for_status()

        data = res.json()
        status = data.get("status")

        logger.info(
            f"[MESHY][STEP 3] Poll #{attempt} "
            f"status={status}"
        )

        if status == "SUCCEEDED":
            model_urls = data.get("model_urls", {})
            glb_url = model_urls.get("glb")

            if not glb_url:
                raise RuntimeError("Meshy SUCCEEDED but glb url missing")

            logger.info("[MESHY][STEP 4] Task succeeded")
            logger.info(f"[MESHY][STEP 4] GLB URL: {glb_url}")

            return glb_url

        if status == "FAILED":
            err = (data.get("task_error") or {}).get("message", "")
            logger.error(f"[MESHY][STEP 4] Task failed: {err}")
            raise RuntimeError(f"Meshy task failed: {err}")

        time.sleep(poll_interval)

    logger.error("[MESHY][STEP 4] Task polling timeout")
    raise TimeoutError("Meshy image-to-3d task timed out")


# =========================================================
# Public API
# =========================================================
def generate_3d(img_url: str) -> str:
    logger.info("[MESHY][START] image-to-3d pipeline started")

    image_data_uri = _minio_image_to_data_uri(img_url)
    task_id = _create_image_to_3d_task(image_data_uri)
    glb_url = _poll_image_to_3d_task(task_id)

    logger.info("[MESHY][END] image-to-3d pipeline finished successfully")
    return glb_url