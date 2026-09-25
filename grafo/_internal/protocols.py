from collections.abc import AsyncGenerator, Awaitable
from typing import Any, Protocol


class OnForwardCallable(Protocol):
    async def __call__(self, forward_data: Any, *args: Any, **kwargs: Any) -> Any: ...


class AwaitableCallback(Protocol):
    def __call__(
        self, *args: Any, **kwargs: Any
    ) -> Awaitable[Any] | AsyncGenerator[Any, None]: ...
