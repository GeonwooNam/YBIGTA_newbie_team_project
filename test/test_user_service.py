import pytest
from app.user.user_service import UserService
from app.user.user_schema import User, UserLogin, UserUpdate
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_user_repository():
    return MagicMock()


@pytest.fixture
def user_service(mock_user_repository):
    return UserService(mock_user_repository)


@pytest.fixture
def test_user():
    return User(email="test@example.com", password="password123", username="TestUser")

def test_login_success(user_service, mock_user_repository, test_user):
    """Test successful login."""
    mock_user_repository.get_user_by_email.return_value = test_user
    user_login = UserLogin(email="test@example.com", password="password123")
    
    result = user_service.login(user_login)
    
    assert result.email == test_user.email
    assert result.username == test_user.username
    mock_user_repository.get_user_by_email.assert_called_once_with("test@example.com")


def test_login_user_not_found(user_service, mock_user_repository):
    """Test login with non-existent user."""
    mock_user_repository.get_user_by_email.return_value = None
    user_login = UserLogin(email="nonexistent@example.com", password="password123")
    
    with pytest.raises(ValueError, match="User not Found."):
        user_service.login(user_login)


def test_login_invalid_password(user_service, mock_user_repository, test_user):
    """Test login with invalid password."""
    mock_user_repository.get_user_by_email.return_value = test_user
    user_login = UserLogin(email="test@example.com", password="wrongpassword")
    
    with pytest.raises(ValueError, match="Invalid ID/PW"):
        user_service.login(user_login)


def test_register_user_success(user_service, mock_user_repository, test_user):
    """Test successful user registration."""
    mock_user_repository.get_user_by_email.return_value = None
    mock_user_repository.save_user.return_value = test_user
    
    result = user_service.register_user(test_user)
    
    assert result.email == test_user.email
    assert result.username == test_user.username
    mock_user_repository.get_user_by_email.assert_called_once_with(test_user.email)
    mock_user_repository.save_user.assert_called_once_with(test_user)


def test_register_user_already_exists(user_service, mock_user_repository, test_user):
    """Test registration with existing user."""
    mock_user_repository.get_user_by_email.return_value = test_user
    
    with pytest.raises(ValueError, match="User already Exists."):
        user_service.register_user(test_user)


def test_delete_user_success(user_service, mock_user_repository, test_user):
    """Test successful user deletion."""
    mock_user_repository.get_user_by_email.return_value = test_user
    mock_user_repository.delete_user.return_value = test_user
    
    result = user_service.delete_user(test_user.email)
    
    assert result.email == test_user.email
    mock_user_repository.get_user_by_email.assert_called_once_with(test_user.email)
    mock_user_repository.delete_user.assert_called_once_with(test_user)


def test_delete_user_not_found(user_service, mock_user_repository):
    """Test deletion of non-existent user."""
    mock_user_repository.get_user_by_email.return_value = None
    
    with pytest.raises(ValueError, match="User not Found."):
        user_service.delete_user("nonexistent@example.com")


def test_update_password_success(user_service, mock_user_repository, test_user):
    """Test successful password update."""
    mock_user_repository.get_user_by_email.return_value = test_user
    mock_user_repository.save_user.return_value = test_user
    
    user_update = UserUpdate(email="test@example.com", new_password="newpassword123")
    result = user_service.update_user_pwd(user_update)
    
    assert result.password == "newpassword123"
    mock_user_repository.get_user_by_email.assert_called_once_with("test@example.com")
    mock_user_repository.save_user.assert_called_once()


def test_update_password_user_not_found(user_service, mock_user_repository):
    """Test password update for non-existent user."""
    mock_user_repository.get_user_by_email.return_value = None
    user_update = UserUpdate(email="nonexistent@example.com", new_password="newpassword123")
    
    with pytest.raises(ValueError, match="User not Found."):
        user_service.update_user_pwd(user_update)
