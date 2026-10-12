from typing import Any, Optional
from fastapi.responses import JSONResponse


def success_response(
    message: str = "Success",
    data: Any = None,
    status_code: int = 200
):
    return {
        "status_code" :status_code,
        "content" :{
            "success": True,
            "message": message,
            "data": data,
            "errors": None
        }}
    


def error_response(
    message: str = "Something went wrong",
    status_code: int = 500,
    errors: Optional[Any] = None
):
    return {
        "status_code" :status_code,
        "content" : {
            "success": False,
            "message": message,
            "data": None,
            "errors": errors
        }
        }
    