# app/api/generate_3d.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.schemas.generate_3d import Generate3DRequest
from app.services.meshy_client import generate_3d
from app.db.session import get_db
from app.db.models.asset import Asset
from app.core.codes import GENERATE_3D_MESSAGE, Generate3DCode

router = APIRouter(prefix="/api/3d", tags=["3D"])


@router.post("/generate")
def generate_3d_asset(
    req: Generate3DRequest,
    db: Session = Depends(get_db),
):
    """
    2D asset_id → 3D GLB 생성
    """

    # =========================================================
    # 1️⃣ 2D Asset 존재 확인
    # =========================================================
    src_asset = (
        db.query(Asset)
        .filter(Asset.asset_id == req.asset_id)
        .first()
    )

    if not src_asset:
        raise HTTPException(status_code=404, detail="Source asset not found")

    # =========================================================
    # 2️⃣ Meshy: 2D → 3D (🔥 asset_id 기반)
    #     반환값: Unity에서 바로 쓸 plain URL
    # =========================================================
    glb_plain_url = generate_3d(req.asset_id, db)

    # =========================================================
    # 3️⃣ DB 저장 (3D asset)
    #     ⚠️ URL ❌ / object key만 저장
    # =========================================================
    # generate_3d 내부에서 사용한 object_key 규칙과 맞춰야 함
    # 예: nodexr-assets/3d/xxxx.glb
    object_key = glb_plain_url.replace(
        "http://localhost:9000/", ""
    )

    asset_3d = Asset(
        node_id=None,
        category_detail_id=None,
        img_url=f"minio:9000/{object_key}",
        type="3D_FINAL",
    )

    db.add(asset_3d)
    db.commit()
    db.refresh(asset_3d)

    # =========================================================
    # 4️⃣ Response (Unity)
    # =========================================================
    return {
        "isSuccess": True,
        "code": Generate3DCode.GENERATE_3D_OK,
        "message": GENERATE_3D_MESSAGE[Generate3DCode.GENERATE_3D_OK],
        "result": {
            "asset_id": asset_3d.asset_id,
            "glb_url": glb_plain_url,
        },
    }