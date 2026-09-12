from user_backend.models import User


user = User(
    id=1001,
    name="Tom",
)


print(user.model_dump())
print(user.model_dump_json())