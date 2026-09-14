from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    description: str
    func: Callable
    input_model: type[BaseModel]
    allow_retry: bool = False
    enabled: bool = True
    groups: set[str] | None = None
