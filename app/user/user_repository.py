from sqlalchemy.orm import Session, DeclarativeBase
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from typing import Optional, cast
from app.user.user_schema import User as UserSchema

# SQLAlchemy 모델 정의 (테이블 이름은 'users')
# Base 정의 방식을 클래스 상속형으로 변경 (mypy 추천 방식)
class Base(DeclarativeBase):
    pass

class UserModel(Base):
    __tablename__ = "users"
    email: Column[str] = Column(String(255), primary_key=True)
    password: Column[str] = Column(String(255), nullable=False)
    username: Column[str] = Column(String(255), nullable=False)


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[UserSchema]:
        # Email로 유저 조회
        user = self.db.query(UserModel).filter(UserModel.email == email).first()
        if user:
            return UserSchema(
                email=cast(str, user.email),
                password=cast(str, user.password),
                username=cast(str, user.username)
            )
        return None

    def save_user(self, user: UserSchema) -> UserSchema:
        # 기존 유저가 있는지 확인 (Update 혹은 Insert 처리)
        db_user = self.db.query(UserModel).filter(UserModel.email == user.email).first()

        if db_user:
            setattr(db_user, "password", user.password)
            setattr(db_user, "username", user.username)
        else:
            db_user = UserModel(email=user.email, password=user.password, username=user.username)
            self.db.add(db_user)

        self.db.commit()
        self.db.refresh(db_user)
        return UserSchema(
            email=cast(str, db_user.email),
            password=cast(str, db_user.password),
            username=cast(str, db_user.username)
        )

    def delete_user(self, user: UserSchema) -> UserSchema:
        # 유저 삭제
        db_user = self.db.query(UserModel).filter(UserModel.email == user.email).first()
        if db_user:
            self.db.delete(db_user)
            self.db.commit()
        return user