import asyncio
from typing import Optional, Type


class _ReentrantAsyncLock:
    """
    A reentrant (recursive) async lock that allows the same task to acquire
    the lock multiple times without blocking.

    This behaves like threading.RLock, but for asyncio-based tasks.

    Usage:
        lock = ReentrantAsyncLock()

        async with lock:
            await some_coroutine()
    """

    def __init__(self) -> None:
        self._lock: asyncio.Lock = asyncio.Lock()
        self._owner: Optional[asyncio.Task] = None
        self._depth: int = 0

    async def acquire(self) -> None:
        """
        Acquire the lock. If the current task already owns it, increase the depth.
        """
        current_task = asyncio.current_task()
        if self._owner == current_task:
            self._depth += 1
            return
        await self._lock.acquire()
        self._owner = current_task
        self._depth = 1

    def release(self) -> None:
        """
        Release the lock. If depth reaches 0, fully release and clear ownership.
        """
        current_task = asyncio.current_task()
        if self._owner != current_task:
            raise RuntimeError("Lock can only be released by the task that acquired it.")
        self._depth -= 1
        if self._depth == 0:
            self._owner = None
            self._lock.release()

    async def __aenter__(self) -> "_ReentrantAsyncLock":
        """
        Enter the async context manager. Acquires the lock.
        """
        await self.acquire()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[BaseException]
    ) -> None:
        """
        Exit the async context manager. Releases the lock.
        """
        self.release()