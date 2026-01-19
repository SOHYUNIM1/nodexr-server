from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from backend.app.core.codes import CategoryCode, CATEGORY_MESSAGE
from backend.app.db.models.category import Category
from backend.app.schemas.category import CategoryListResp, CategorySelectReq
from backend.app.schemas.response import ApiResponse

router = APIRouter(prefix="/api/categories", tags=["Categories"])

@router.get("", response_model=ApiResponse)
def list_categories(
    room_id: str,
    db: Session = Depends(get_db)
):
    categories = db.query(Category).filter(Category.room_id == room_id).all()

    result_dto = [
        CategoryListResp(
            category_id=c.category_id,
            category_name=c.category_name
        )
        for c in categories
    ]

    return ApiResponse(
        code=CategoryCode.CAT_LIST_OK,
        message=CATEGORY_MESSAGE[CategoryCode.CAT_LIST_OK],
        result={
            "categories": result_dto
        }
    )



@router.post("/select", response_model=ApiResponse)
def select_categories(
    req: CategorySelectReq,
    db: Session = Depends(get_db)
):
    
    curr_category = db.query(Category).filter(
        Category.room_id == req.room_id,
        Category.category_id == req.category_id
    ).first()

    pre_category = db.query(Category).filter(
        Category.room_id == req.room_id,
        Category.phase == "ACTIVE"
    ).first()

    if pre_category:
        pre_category.phase = "INACTIVE"

    curr_category.phase = "ACTIVE"

    db.commit()

    return ApiResponse(
        code=CategoryCode.CAT_SELECT,
        message=CATEGORY_MESSAGE[CategoryCode.CAT_SELECT],
        result={
            "category_name": curr_category.category_name
        }
    )
