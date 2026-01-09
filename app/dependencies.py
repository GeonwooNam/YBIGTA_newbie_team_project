from fastapi import Depends
from app.user.user_repository import UserRepository
from app.user.user_service import UserService

def get_user_repository() -> UserRepository:
    return UserRepository()

def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)
