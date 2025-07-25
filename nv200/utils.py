import configparser
from pathlib import Path
from datetime import datetime
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


class DeviceParamFile:
    """
    A class to encapsulate reading and writing device parameters
    to and from an INI file with metadata.

    The INI file will include:
    - [Device Parameters]: The main key-value pairs for device settings
    - [Meta Data]: A timestamp for when the data was exported
    """

    DEVICE_SECTION: str = "Device Parameters"
    META_SECTION: str = "Meta Data"

    def __init__(self, parameters: dict[str, str], timestamp: Optional[str] = None) -> None:
        """
        Initialize the DeviceParamFile.

        Args:
            parameters (Dict[str, str]): The device parameters as key-value pairs.
            timestamp (Optional[str]): Optional export timestamp. If not provided, current time is used.
        """
        self.parameters: dict[str, str] = parameters
        self.timestamp: str = timestamp or datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

    def write(self, filepath: Path) -> None:
        """
        Write the device parameters and metadata to an INI file.

        Args:
            filepath (Path): The full path to the INI file to write.
        """
        config = configparser.ConfigParser()
        config[self.DEVICE_SECTION] = self.parameters
        config[self.META_SECTION] = {"export_timestamp": self.timestamp}

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with filepath.open("w", encoding="utf-8") as f:
            config.write(f)

    @classmethod
    def read(cls, filepath: Path, allowed_keys: Optional[set[str]] = None) -> "DeviceParamFile":
        """
        Read device parameters and metadata from an INI file.

        Args:
            filepath (Path): The path to the INI file to read.
            allowed_keys (Optional[set[str]]): If provided, only keys in this set will be included.

        Returns:
            DeviceParamFile: An instance containing the filtered parameters and metadata.

        Raises:
            ValueError: If the required device parameter section is missing.
        """
        config = configparser.ConfigParser()
        config.read(filepath, encoding="utf-8")

        if cls.DEVICE_SECTION not in config:
            raise ValueError(f"Missing section: '{cls.DEVICE_SECTION}' in {filepath}")

        # Get and optionally filter the parameters
        parameters = dict(config[cls.DEVICE_SECTION])
        if allowed_keys is not None:
            parameters = {k: v for k, v in parameters.items() if k in allowed_keys}

        timestamp: str = config.get(cls.META_SECTION, "export_timestamp", fallback="")

        return cls(parameters=parameters, timestamp=timestamp)
