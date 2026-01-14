from app.user.user_repository import UserRepository
from app.user.user_schema import User, UserLogin, UserUpdate
from pydantic import EmailStr
from typing import Optional

class UserService:
    def __init__(self, userRepository: UserRepository) -> None:
        self.repo: UserRepository = userRepository

    def login(self, user_login: UserLogin) -> User:
        ## TODO
        """
        사용자의 이메일과 비밀번호를 확인하여 로그인을 처리합니다.

        Args:
            user_login (UserLogin): 로그인 시 필요한 이메일과 비밀번호 정보를 담은 객체.

        Returns:
            User: 인증에 성공한 사용자의 정보 객체.

        Raises:
            ValueError: 해당 이메일의 사용자가 없거나 비밀번호가 일치하지 않을 경우 발생합니다.
        """
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
        """
        이메일 주소를 기반으로 특정 사용자를 시스템에서 삭제합니다.

        Args:
            email (str): 삭제하려는 사용자의 이메일 주소.

        Returns:
            User: 삭제 처리가 완료된 사용자의 데이터 객체.

        Raises:
            ValueError: 삭제하려는 사용자가 데이터베이스에 존재하지 않을 경우 발생합니다.
        """
        ## TODO        
        deleted_user: Optional[User] = self.repo.get_user_by_email(email)
        if deleted_user is None:
            raise ValueError("User not Found.")
        deleted_user = self.repo.delete_user(deleted_user)
        return deleted_user

    def update_user_pwd(self, user_update: UserUpdate) -> User:
        ## TODO
        """
        사용자의 기존 비밀번호를 새로운 비밀번호로 업데이트합니다.

        Args:
            user_update (UserUpdate): 비밀번호 변경 대상의 이메일과 새 비밀번호를 포함한 객체.

        Returns:
            User: 비밀번호 업데이트 및 저장이 완료된 사용자 객체.

        Raises:
            ValueError: 업데이트하려는 사용자를 찾을 수 없는 경우 발생합니다.
        """
        email: EmailStr = user_update.email
        new_password: str = user_update.new_password
        updated_user: Optional[User] = self.repo.get_user_by_email(email)
        if updated_user is None:
            raise ValueError("User not Found.")
        updated_user.password = new_password 
        updated_user = self.repo.save_user(updated_user)
        return updated_user
        