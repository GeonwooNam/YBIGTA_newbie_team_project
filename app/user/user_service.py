from app.user.user_repository import UserRepository
from app.user.user_schema import User, UserLogin, UserUpdate
from pydantic import EmailStr
from typing import Optional

class UserService:
    def __init__(self, userRepository: UserRepository) -> None:
        self.repo: UserRepository = userRepository

    def login(self, user_login: UserLogin) -> User:
        ## TODO
        email: EmailStr = user_login.email 
        password: str = user_login.password
        user: Optional[User] = self.repo.get_user_by_email(email)
        if user is None:
            raise ValueError("User not Found.")
        if password != user.password:
            raise ValueError("Invalid ID/PW")
        return user
        
    def register_user(self, new_user: User) -> User:
        new_email: EmailStr = new_user.email
        if self.repo.get_user_by_email(new_email) is not None:
            raise ValueError("User already Exists.")
        new_user = self.repo.save_user(new_user)
        return new_user

    def delete_user(self, email: str) -> User:
        ## TODO        
        deleted_user: Optional[User] = self.repo.get_user_by_email(email)
        if deleted_user is None:
            raise ValueError("User not Found.")
        deleted_user = self.repo.delete_user(deleted_user)
        return deleted_user

    def update_user_pwd(self, user_update: UserUpdate) -> User:
        ## TODO
        email: EmailStr = user_update.email
        new_password: str = user_update.new_password
        updated_user: Optional[User] = self.repo.get_user_by_email(email)
        if updated_user is None:
            raise ValueError("User not Found.")
        updated_user.password = new_password 
        updated_user = self.repo.save_user(updated_user)
        return updated_user
        