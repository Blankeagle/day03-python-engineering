from collections.abc import Callable


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        self._tools[name] = func

    def get(self, name: str):
        return self._tools.get(name)

    def execute(self, name: str, arguments: dict):
        func = self.get(name)

        if func is None:
            raise ValueError(f"Tool not found: {name}")

        return func(**arguments)