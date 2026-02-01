from fastapi import Depends
from database.mysql_connection import SessionLocal
from app.user.user_repository import UserRepository
from app.user.user_service import UserService

# MySQL DB 세션을 생성하고 관리하는 Generator 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# UserRepository에 DB 세션을 주입하여 반환
def get_user_repo(db = Depends(get_db)):
    return UserRepository(db)

def get_user_repository() -> UserRepository:
    return UserRepository()

def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)