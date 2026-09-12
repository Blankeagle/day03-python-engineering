from user_backend.models import User


class UserService:

    def __init__(self) -> None:
        self.users: dict[int, User] = {}

    def create_user(self, user: User) -> User:
        self.users[user.id] = user
        return user

    def get_user(self, user_id: int) -> User | None:
        return self.users.get(user_id)

    def list_users(self) -> list[User]:
        return list(self.users.values())