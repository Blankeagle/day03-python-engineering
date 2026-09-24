from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class AgentTrace:
    # Identify one workflow execution
    thread_id: str

    # Store trace events in execution order
    events: list[dict[str, Any]] = field(default_factory=list)

    def add_event(
        self,
        event: str,
        **data: Any,
    ) -> None:
        # Append one trace event with its UTC timestamp
        self.events.append(
            {
                "event": event,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **data,
            }
        )