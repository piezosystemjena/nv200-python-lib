import asyncio
from typing import Callable, Awaitable, Optional

async def wait_until(
    condition_func: Callable[[], Awaitable],  # Can return any type
    check_func: Callable[[any], bool],  # A function that checks if the value meets the condition
    poll_interval_s: float = 0.1,  # Time interval in seconds to wait between condition checks
    timeout_s: Optional[float] = None  # Timeout in seconds
) -> bool:
    """
    Wait until an asynchronous condition function returns a value that satisfies a check function.

    Args:
        condition_func (Callable[[], Awaitable]): An async function returning a value of any type.
        check_func (Callable[[any], bool]): A function that checks if the value returned by
                                             condition_func satisfies the condition.
        poll_interval_s (float): Time in seconds to wait between condition checks.
        timeout_s (float | None): Optional timeout in seconds. If None, wait indefinitely.

    Returns:
        bool: True if the condition matched within the timeout, False otherwise.

    Example:
        >>> async def get_result():
        ...     return 3
        >>> await wait_until(get_result, check_func=lambda x: x > 2, timeout_s=5.0)
        True
    """
    start = asyncio.get_event_loop().time()

    while True:
        result = await condition_func()
        if check_func(result):
            return True
        if timeout_s is not None and asyncio.get_event_loop().time() - start >= timeout_s:
            return False
        await asyncio.sleep(poll_interval_s)