from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Generic, Protocol, Self, TypeVar

T = TypeVar("T")


@dataclass
class AnyValueOf(Generic[T]):
    klass: type[T]

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, self.klass):
            return self.rules(other)
        return False

    def rules(self, other: T) -> bool:
        return True


class SupportsSub(Protocol):
    @abstractmethod
    def __gt__(self, other: Self) -> bool: ...


U = TypeVar("U", bound=SupportsSub)


@dataclass
class AnyBetween(AnyValueOf[U]):
    before: U
    after: U

    def rules(self, other: U) -> bool:
        return self.before < other < self.after


@dataclass
class AnyDateAround(AnyValueOf[datetime]):
    at: datetime = field(default_factory=lambda: datetime.now())
    seconds: int = 1

    def rules(self, other: datetime) -> bool:
        return self.at - timedelta(seconds=self.seconds) < other < self.at
