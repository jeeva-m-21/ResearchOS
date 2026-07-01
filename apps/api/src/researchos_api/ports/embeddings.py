from collections.abc import Sequence
from typing import Protocol


class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...
