from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class ProviderError(Exception):
    pass


@dataclass
class ProviderResult:
    model_used: str
    content: str
    tokens_in: int
    tokens_out: int
    provider_name: str


class BaseProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str, model: str, timeout_seconds: int) -> ProviderResult:
        raise NotImplementedError
