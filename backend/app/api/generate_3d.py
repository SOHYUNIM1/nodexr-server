from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import requests
from io import BytesIO
import uuid

from app.schemas.generate_3d import Generate3DRequest
from app.services.meshy_client import generate_3d
from app.storage.minio import minio_client, generate_presigned_url
from app.db.session import get_db
from app.db.models.asset import Asset
from app.core.codes import GENERATE_3D_MESSAGE, Generate3DCode

router = APIRouter(prefix="/api/3d", tags=["3D"])


@router.post("/generate")
def generate_3d_asset(
    req: Generate3DRequest,
    db: Session = Depends(get_db),
):
    # =========================================================
    # 1️⃣ Meshy: 2D → 3D
    # =========================================================
    glb_url = generate_3d(req.img_url)

    # =========================================================
    # 2️⃣ (선택) GLB → MinIO 저장
    #     ※ Meshy CDN 의존 제거 목적
    # =========================================================
    res = requests.get(glb_url, stream=True, timeout=60)
    res.raise_for_status()

    object_name = f"3d/{uuid.uuid4()}.glb"

    minio_client.put_object(
        bucket_name="nodexr-assets",
        object_name=object_name,
        data=res.raw,
        length=-1,
        part_size=10 * 1024 * 1024,
        content_type="model/gltf-binary",
    )

    minio_3d_url = generate_presigned_url(
        bucket="nodexr-assets",
        object_name=object_name,
    )

    # =========================================================
    # 3️⃣ DB 저장 (node 연결 ❌)
    # =========================================================
    asset = Asset(
        node_id=None,
        category_detail_id=None,
        img_url=minio_3d_url,
        type="3D",
    )
    db.add(asset)
    db.commit()

    # =========================================================
    # 4️⃣ Response
    # =========================================================
    return {
        "isSuccess": True,
        "code": Generate3DCode.GENERATE_3D_OK,
        "message": GENERATE_3D_MESSAGE[Generate3DCode.GENERATE_3D_OK],
        "result": {
            "img_url": minio_3d_url,
        },
    }