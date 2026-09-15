from pydantic import BaseModel, Field

class UserMemory(BaseModel):
    user_id: str = Field(
        min_length=1,
        max_length=100,
    )

    name: str | None = None
    occupation: str | None = None
    response_preference: str | None = None

    def to_prompt(self) -> str:
        items = []

        if self.name:
            items.append(f"Name: {self.name}")

        if self.occupation:
            items.append(f"Occupation: {self.occupation}")

        if self.response_preference:
            items.append(
                f"Response preference: {self.response_preference}"
            )

        if not items:
            return ""

        return "\n".join(items)

class MemoryUpdate(BaseModel):
    name: str | None = None
    occupation: str | None = None
    response_preference: str | None = None

    forget_fields: list[str] = Field(
        default_factory=list
    )
