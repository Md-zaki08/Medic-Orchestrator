from abc import ABC, abstractmethod
from typing import Any


class BaseMedicAgent(ABC):
    agent_name: str = "base"

    @abstractmethod
    async def execute(self, state: Any) -> Any:
        pass
