from fastapi import APIRouter, HTTPException, Depends, status
from app.user.user_schema import User, UserLogin, UserUpdate, UserDeleteRequest
from app.user.user_service import UserService
from app.dependencies import get_user_service
from app.responses.base_response import BaseResponse

user = APIRouter(prefix="/api/user")


@user.post("/login", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def login_user(user_login: UserLogin, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    try:
        user = service.login(user_login)
        return BaseResponse(status="success", data=user, message="Login Success.") 
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@user.post("/register", response_model=BaseResponse[User], status_code=status.HTTP_201_CREATED)
def register_user(user: User, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    ## TODO
    """
    시스템에 새로운 사용자를 등록합니다.

    Args:
        user (User): 이메일, 사용자 이름, 비밀번호를 포함한 사용자 데이터.
        service (UserService): FastAPI에 의해 주입된 사용자 서비스 인스턴스.

    Returns:
        BaseResponse[User]: 생성된 사용자 데이터를 포함한 성공 응답.

    Raises:
        HTTPException: 사용자가 이미 존재하거나 유효성 검사에 실패한 경우 400 에러를 발생시킵니다.
    """
    try:
        user = service.register_user(user)
        return BaseResponse(status="success", data=user, message="User registeration success.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@user.delete("/delete", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def delete_user(user_delete_request: UserDeleteRequest, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    ## TODO
    """
    제공된 이메일을 기반으로 사용자 계정을 삭제합니다.

    Args:
        user_delete_request (UserDeleteRequest): 삭제할 사용자의 이메일을 포함한 요청 본문.
        service (UserService): FastAPI에 의해 주입된 사용자 서비스 인스턴스.

    Returns:
        BaseResponse[User]: 삭제된 사용자의 정보를 포함한 성공 응답.

    Raises:
        HTTPException: 사용자를 찾을 수 없는 경우 404 에러를 발생시킵니다.
    """
    try:
        user: User = service.delete_user(user_delete_request.email)
        return BaseResponse(status="success", data=user, message="User Deletion Success.")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@user.put("/update-password", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def update_user_password(user_update: UserUpdate, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    ## TODO
    """
    기존 사용자의 비밀번호를 업데이트합니다.

    Args:
        user_update (UserUpdate): 사용자의 이메일과 새 비밀번호를 포함한 데이터.
        service (UserService): FastAPI에 의해 주입된 사용자 서비스 인스턴스.

    Returns:
        BaseResponse[User]: 업데이트된 사용자 정보를 포함한 성공 응답.

    Raises:
        HTTPException: 사용자를 찾을 수 없거나 업데이트에 실패한 경우 404 에러를 발생시킵니다.
    """
    try:
        user: User = service.update_user_pwd(user_update)
        return BaseResponse(status="success", data=user, message="User password update success.")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
