from fastapi import APIRouter, Depends

from app.controllers.auth_controller import AuthController
from app.schemas.requests.auth_request import LoginRequest
from app.schemas.requests.auth_request import UserResponse
from app.core.security import get_current_user, require_authenticated_user
from app.utils.response import success_response, error_response


router = APIRouter()


@router.post("/login")
async def login(body: LoginRequest):
    return await AuthController.login(body)


# @router.post("/logout")
# async def logout():
#     return await AuthController.logout()


@router.get("/me")
async def get_me(current_user=Depends(require_authenticated_user)):
    try:
        data = current_user
        return success_response(
            message="Success",
            data=data,
            status_code=200
        )
    except Exception as e:
        return error_response(message=str(e), status_code=401)
  