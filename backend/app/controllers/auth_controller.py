
from app.services.auth_service import AuthService
from app.schemas.requests.auth_request import LoginRequest, TokenResponse
from app.utils.response import success_response, error_response



auth_service = AuthService()


class AuthController:

    async def login(body: LoginRequest) -> TokenResponse:
        try:
            data= await auth_service.login(body)
            return success_response(
            message="Success",
            data=data,
            status_code=201
        )

        except Exception as e:
            return error_response(message=str(e),status_code=400)


