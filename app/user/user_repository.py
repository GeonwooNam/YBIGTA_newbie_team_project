from sqlalchemy.orm import Session
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from typing import Optional
from app.user.user_schema import User as UserSchema

# SQLAlchemy 모델 정의 (테이블 이름은 'users')
Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"
    email = Column(String(255), primary_key=True)
    password = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[UserSchema]:
        # Email로 유저 조회
        user = self.db.query(UserModel).filter(UserModel.email == email).first()
        if user:
            return UserSchema(email=user.email, password=user.password, username=user.username)
        return None

    def save_user(self, user: UserSchema) -> UserSchema:
        # 기존 유저가 있는지 확인 (Update 혹은 Insert 처리)
        db_user = self.db.query(UserModel).filter(UserModel.email == user.email).first()

        if db_user:
            db_user.password = user.password
            db_user.username = user.username
        else:
            db_user = UserModel(email=user.email, password=user.password, username=user.username)
            self.db.add(db_user)

        self.db.commit()
        self.db.refresh(db_user)
        return UserSchema(email=db_user.email, password=db_user.password, username=db_user.username)

    def delete_user(self, user: UserSchema) -> UserSchema:
        # 유저 삭제
        db_user = self.db.query(UserModel).filter(UserModel.email == user.email).first()
        if db_user:
            self.db.delete(db_user)
            self.db.commit()
        return user