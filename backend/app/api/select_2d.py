from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.schemas.response import ApiResponse
from app.core.ws_manager import graph_ws_manager

from app.db.models.node import Node
from app.db.models.asset import Asset
from app.db.models.category_detail import CategoryDetail
from app.schemas.select_2d import Select2DRequest
from app.core.codes import Select2DCode, SELECT_2D_MESSAGE

router = APIRouter(prefix="/api/2d", tags=["2D Select"])


@router.post("/select", response_model=ApiResponse)
def select_2d_image(
    req: Select2DRequest,
    db: Session = Depends(get_db),
):
    # -------------------------------------------------
    # 1️⃣ 선택된 asset 조회 (node_id 기준)
    # -------------------------------------------------
    selected_asset = (
        db.query(Asset)
        .filter(Asset.node_id == req.node_id)
        .first()
    )

    if not selected_asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # -------------------------------------------------
    # 2️⃣ 같은 room의 기존 CORE → CANDIDATE로 변경
    # -------------------------------------------------
    node_ids_in_room = (
        db.query(Node.node_id)
        .filter(Node.room_id == req.room_id)
        .subquery()
    )

    db.query(Asset) \
      .filter(Asset.node_id.in_(node_ids_in_room)) \
      .filter(Asset.type == "CURR_2D_CORE") \
      .update(
          {"type": "2D_CANDIDATE"},
          synchronize_session=False
      )

    # -------------------------------------------------
    # 3️⃣ 선택된 asset → CURR_2D_CORE
    # -------------------------------------------------
    selected_asset.type = "CURR_2D_CORE"

    db.commit()

    # -------------------------------------------------
    # 4️⃣ 응답
    # -------------------------------------------------
    return ApiResponse(
        code="2D200",
        message="2D 코어 이미지 선택 성공",
        result={
            "category_detail_id": selected_asset.category_detail_id,
            "asset_id": selected_asset.asset_id,
        }
    )