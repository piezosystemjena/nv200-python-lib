import asyncio
from typing import Generator, Callable, Awaitable, Optional

class TimeSeries:
    """
    TimeSeries represents waveform data with amplitude values (values) and corresponding sample times (sample_times_ms).
    It also includes a sample time in milliseconds.
    """
    
    def __init__(self, values: list, sample_time_ms: int):
        """
        Initialize the TimeSeries instance with amplitude values and sample time.
        
        Args:
            values (list): The amplitude values corresponding to the waveform.
            sample_time_ms (int): The sample time in milliseconds (sampling interval).
        """
        self._values = values
        self._sample_time_ms = sample_time_ms

    @property
    def sample_time_ms(self) -> float:
        """Returns the sample time in milliseconds."""
        return self._sample_time_ms
    
    @property
    def values(self) -> list:
        """Return the amplitude values (values) as a list."""
        return self._values

    @values.setter
    def values(self, values: list) -> None:
        """Set the amplitude values (values)."""
        self._values = values

    def generate_sample_times_ms(self) -> Generator[float, None, None]:
        """
        Generator function to return time (sample_times_ms) values as they are requested.
        This will calculate and yield the corresponding time values based on sample_time_us.
        """
        for i in range(len(self.values)):
            yield i * self._sample_time_ms

    @property
    def sample_times_ms(self) -> list:
        """
        Return all time (sample_times_ms) values as a list, calculated based on the sample time.
        """
        return list(self.generate_sample_times_ms())
    
    def __str__(self):
        """
        Return a string representation of the TimeSeries object, showing pairs of time and value.
        Example: [(0, 1.2), (10, 2.5), (20, 3.7), ...]
        """
        time_value_pairs = list(zip(self.sample_times_ms, self.values))
        return f"TimeSeries({time_value_pairs})"


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