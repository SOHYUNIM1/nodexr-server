from typing import TypeVar, Optional
from app.schemas.response import ApiResponse

T = TypeVar("T")


def success_response(
    *,
    code: str,
    message: str,
    result: Optional[T] = None,
) -> ApiResponse[T]:
    return ApiResponse(
        isSuccess=True,
        code=code,
        message=message,
        result=result,
    )


def error_response(
    *,
    code: str,
    message: str,
) -> ApiResponse[None]:
    return ApiResponse(
        isSuccess=False,
        code=code,
        message=message,
        result=None,
    )