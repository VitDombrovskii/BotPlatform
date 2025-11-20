from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseStorage(ABC):
    """
    Абстракция над хранилищем данных платформы.

    Конкретные реализации могут использовать:
    - файлы
    - Redis
    - PostgreSQL
    - любую другую систему хранения.
    """

    @abstractmethod
    def save_state(self, key: str, state: Dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_state(self, key: str) -> Dict[str, Any] | None:
        raise NotImplementedError


class InMemoryStorage(BaseStorage):
    """
    Простая in-memory реализация для отладки и тестов.
    """

    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}

    def save_state(self, key: str, state: Dict[str, Any]) -> None:
        self._data[key] = state

    def load_state(self, key: str) -> Dict[str, Any] | None:
        return self._data.get(key)
