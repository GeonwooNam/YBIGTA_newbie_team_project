import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.user.user_schema import User, UserLogin, UserUpdate, UserDeleteRequest
from app.responses.base_response import BaseResponse
from app.user.user_repository import UserRepository
from app.user.user_service import UserService
from app.dependencies import get_user_service

# FastAPI 테스트 클라이언트
client = TestClient(app)

# ERROR
USER_NOT_FOUND = "User not Found."
USER_ALREADY_EXISTS = "User already Exists."

# Mock 데이터
mock_user = User(email="test@example.com", password="password123", username="TestUser")


# Mock UserService 생성
@pytest.fixture
def mock_user_service():
    with patch("app.user.user_service.UserService") as mock_service:
        yield mock_service


# 모든 테스트에서 의존성 오버라이드
@pytest.fixture(autouse=True)
def override_dependencies(mock_user_service):
    app.dependency_overrides[get_user_service] = lambda: mock_user_service.return_value
    yield
    app.dependency_overrides = {}


# Mock UserRepository 생성
@pytest.fixture
def mock_user_repository():
    return MagicMock(spec=UserRepository)


# 테스트: 회원가입 성공
def test_register_user_success(mock_user_service):

    new_user = User(email="unique@example.com", password="password123", username="TestUser")
    
    # 실행
    mock_user_service.return_value.register_user.return_value = new_user

    response = client.post("/api/user/register", json=mock_user.model_dump())
    # 검증
    data = response.json()
    assert data["data"]["email"] == new_user.email
    assert data["data"]["username"] == new_user.username


# 테스트: 회원가입 실패 (이미 존재하는 유저)
def test_register_user_already_exists(mock_user_service):
    mock_user_service.return_value.register_user.side_effect = ValueError(USER_ALREADY_EXISTS)

    response = client.post("/api/user/register",json=mock_user.model_dump())

    # 검증
    assert response.status_code == 400
    assert response.json()["detail"] == USER_ALREADY_EXISTS


# 테스트: 로그인 성공
def test_login_success(mock_user_service):
    mock_user_service.return_value.login.return_value = mock_user

    user_login = UserLogin(email=mock_user.email, password=mock_user.password)
    response = client.post("/api/user/login", json=user_login.model_dump())

    # 검증
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["email"] == mock_user.email
    assert data["data"]["username"] == mock_user.username


# 테스트: 로그인 실패 (유저 없음)
def test_login_user_not_found(mock_user_service):
    mock_user_service.return_value.login.side_effect = ValueError(USER_NOT_FOUND)

    user_login = UserLogin(email="nonexistent@example.com", password="password123")
    response = client.post("/api/user/login", json=user_login.model_dump())

    # 검증
    assert response.status_code == 400
    assert response.json()["detail"] == USER_NOT_FOUND


# 테스트: 비밀번호 업데이트 성공
def test_update_password_success(mock_user_service):
    updated_user = User(email="test@example.com", password="newpassword123", username="TestUser")
    user_update = UserUpdate(email=updated_user.email, new_password=updated_user.password)

    mock_user_service.return_value.update_user_pwd.return_value = updated_user

    response = client.put(
        "/api/user/update-password",
        json=user_update.model_dump()
    )

    # 검증
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["email"] == updated_user.email
    assert data["data"]["password"] == updated_user.password


# 테스트: 비밀번호 업데이트 실패 (유저 없음)
def test_update_password_user_not_found(mock_user_service):
    mock_user_service.return_value.update_user_pwd.side_effect = ValueError(USER_NOT_FOUND)

    user_update = UserUpdate(email="nonexistent@example.com", new_password="password123")
    response = client.put("/api/user/update-password", json=user_update.model_dump())

    # 검증
    assert response.status_code == 404
    assert response.json()["detail"] == USER_NOT_FOUND


# 테스트: 유저 삭제 성공
def test_delete_user_success(mock_user_service):
    mock_user_service.return_value.delete_user.return_value = mock_user

    user_delete_request = UserDeleteRequest(email=mock_user.email)
    response = client.request("DELETE","/api/user/delete",json=user_delete_request.model_dump())

    # 검증
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["email"] == mock_user.email


# 테스트: 유저 삭제 실패 (유저 없음)
def test_delete_user_not_found(mock_user_service):
    # delete_user 메서드가 명시적으로 ValueError를 발생시킴
    mock_user_service.return_value.delete_user.side_effect = ValueError(USER_NOT_FOUND)
    not_exist_user = UserDeleteRequest(email=mock_user.email)
    # DELETE 요청
    response = client.request("DELETE","/api/user/delete", json=not_exist_user.model_dump())
    # 응답 검증
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == USER_NOT_FOUND