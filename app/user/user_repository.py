import json

from typing import Dict, Optional

from app.user.user_schema import User
from app.config import USER_DATA

class UserRepository:
    def __init__(self) -> None:
        self.users: Dict[str, dict] = self._load_users()

    def _load_users(self) -> Dict[str, Dict]:
        try:
            with open(USER_DATA, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            raise ValueError("File not found")

    def get_user_by_email(self, email: str) -> Optional[User]:
        user = self.users.get(email)
        return User(**user) if user else None

    def save_user(self, user: User) -> User: 
        self.users[user.email] = user.model_dump()
        with open(USER_DATA, "w") as f:
            json.dump(self.users, f)
        return user

    def delete_user(self, user: User) -> User:
        del self.users[user.email]
        with open(USER_DATA, "w") as f:
            json.dump(self.users, f)
        return user