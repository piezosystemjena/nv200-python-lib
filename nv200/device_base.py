"""
Provides classes and enumerations for communicating with and interpreting responses from NV200 devices.

This module includes an asynchronous client for issuing commands and parsing responses
from NV200 devices over supported transport protocols (e.g., serial, Telnet).
"""

import asyncio
import logging
from typing import Dict, Type, List, TypeVar, Union
from nv200.transport_protocol import TransportProtocol
from nv200._internal._reentrant_lock import _ReentrantAsyncLock
from nv200.shared_types import (
    ErrorCode,
    DeviceError,
    DetectedDevice,
    DeviceInfo
)

# Global module locker
logger = logging.getLogger(__name__)

class PiezoDeviceBase:
    """
    Generic piezosystem device base class.

    PiezoDeviceBase provides an asynchronous interface for communicating with a piezoelectric device
    over various transport protocols (such as serial or telnet). It encapsulates low-level device commands,
    response parsing, synchronization mechanisms, and optional command result caching.

    This class is intended to be subclassed by concrete device implementations (e.g., `NV200Device`),
    which define specific device behaviors and cacheable commands.

    Concrete device classes support caching of command parameters/values. This mechanism is designed 
    to reduce frequent read access over the physical communication interface by serving previously 
    retrieved values from a local cache. Since each read operation over the interface introduces latency, 
    caching can significantly improve the performance of parameter access — particularly in scenarios 
    like graphical user interfaces where many values are queried repeatedly.

    Note:
        Caching should only be used if it is guaranteed that no other external application modifies the 
        device state in parallel. For example, if access is made via the Python library over a Telnet 
        connection, no other software (e.g., via a serial interface) should modify the same parameters 
        concurrently. In such multi-access scenarios, caching can lead to inconsistent or outdated data. 
        To ensure correctness, disable caching globally by setting the class variable 
        `CMD_CACHE_ENABLED` to ``False``.

    Attributes:
        CMD_CACHE_ENABLED (bool): 
            Class-level flag that controls whether command-level caching is enabled. When set to True 
            (default), values read from or written to the device for cacheable commands will be stored 
            and retrieved from an internal cache. Setting this to ``False`` disables the caching 
            behavior globally for all instances unless explicitly overridden at the instance level.
    """
    CMD_CACHE_ENABLED = True  # Enable command caching by default - set to False to disable caching
    CACHEABLE_COMMANDS: set[str] = set() # set of commands that can be cached
    DEFAULT_TIMEOUT_SECS = 0.6
    DEVICE_ID = None # Placeholder for device ID, to be set in subclasses
    _help_dict: dict[str, str] = {}  # Dictionary to store help information for commands
    
    def __init__(self, transport: TransportProtocol):
        self._transport : TransportProtocol = transport
        self._lock = _ReentrantAsyncLock()
        self._cache: Dict[str, str] = {}
        self.frame_delimiter_write : str= "\r\n"  # Default frame delimiter for writing commands

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.DEVICE_ID:
            DEVICE_MODEL_REGISTRY[cls.DEVICE_ID] = cls

    @property
    def lock(self) -> _ReentrantAsyncLock:
        """
        Lock that can be used by external code to synchronize access to the device.

        Use with ``async with client.lock:`` to group operations atomically.
        """
        return self._lock
    
    @property 
    def transport_protocol(self) -> TransportProtocol:
        """
        Returns the transport protocol used by the device.
        """
        return self._transport

    async def _read_raw_message(self, timeout_param : float = DEFAULT_TIMEOUT_SECS) -> str:
        """
        Asynchronously reads a response from the transport layer with a specified timeout.
        """
        return await self._transport.read_message(timeout_param)
        

    def _parse_response(self, response: str) -> tuple[str, List[str]]:
        """
        Parses the response from the device and extracts the command and parameters.
        If the response indicates an error (starts with "error"), it raises a DeviceError
        with the corresponding error code. If the error code is invalid or unspecified,
        a default error code of 1 is used.
        Args:
            response (bytes): The response received from the device as a byte string.
        Returns:
            tuple: A tuple containing the command (str) and a list of parameters (list of str).
        Raises:
            DeviceError: If the response indicates an error.
        """
        # Check if the response indicates an error
        if response.startswith("error"):
            parts = response.split(',', 1)
            if len(parts) > 1:
                try:
                    error_code = int(parts[1].strip("\x01\n\r\x00"))
                    # Raise a DeviceError with the error code
                    raise DeviceError(ErrorCode.from_value(error_code))
                except ValueError:
                    # In case the error code isn't valid
                    raise DeviceError(1)  # Default error: Error not specified
            else:
                raise DeviceError(1)  # Default error: Error not specified
        else:
            # Normal response, split the command and parameters
            parts = response.split(',', 1)
            command = parts[0].strip()
            parameters = []
            if len(parts) > 1:
                parameters = [param.strip("\x01\n\r\x00") for param in parts[1].split(',')]
            return command, parameters
        

    async def connect(self, auto_adjust_comm_params: bool = True):
        """
        Establishes a connection using the transport layer.

        This asynchronous method initiates the connection process by calling
        the `connect` method of the transport instance.

        Args:
            auto_adjust_comm_params (bool): If True, the Telnet transport will
                automatically adjust the internal communication parameters of
                the XPORT ethernet module. It will set the flow control mode to#
                ``XON_XOFF_PASS_TO_HOST``. This is required for the library to work+
                properly.

        Raises:
            Exception: If the connection fails, an exception may be raised
                       depending on the implementation of the transport layer.
        """
        await self._transport.connect(auto_adjust_comm_params, self)
        is_match, detected_id = await self.check_device_type()
        if not is_match:
            await self._transport.close()
            raise RuntimeError(
                f"Device type mismatch: expected {self.DEVICE_ID}, got {detected_id}. "
                "Please check the device connection and ensure the correct device is connected."
            )

    async def write(self, cmd: str):
        """
        Sends a command to the transport layer.

        This asynchronous method writes a command string followed by a carriage return
        to the transport layer.

        Args:
            cmd (str): The command string to be sent. No carriage return is needed. 

        Example:
            >>> await device_client.write('set,80') 
        """
        logger.debug("Writing cmd.: %s", cmd)

        async with self.lock:
            await self._transport.write(cmd + self.frame_delimiter_write)
            try:
                response = await self._transport.read_message(timeout=0.4)
                return self._parse_response(response)
            except asyncio.TimeoutError:
                return None  # Or handle it differently
        

    async def write_value(self, cmd: str, value: Union[int, float, str, bool]):
        """
        Asynchronously writes a value to the device using the specified command.

        Args:
            cmd (str): The command string to send to the device.
            value (Union[int, float, str, bool]): The value to write, which can be an integer, float, string, or boolean.

        Example:
            >>> await device_client.write('set', 80)
        """

        # Convert boolean to int internally
        if isinstance(value, bool):
            value_to_write = int(value)
        else:
            value_to_write = value

        # Always use %f for logging value
        logger.debug("Writing value: %s,%f", cmd, float(value_to_write))
        await self.write(f"{cmd},{value_to_write}")

        if self.CMD_CACHE_ENABLED and cmd in self.CACHEABLE_COMMANDS:
            logger.debug("Caching write value: %s,%f", cmd, float(value_to_write))
            self._cache[cmd] = str(value_to_write)
        
       
    async def write_string_value(self, cmd: str, value: str):
        """
        Sends a command with a string value to the transport layer.

        This asynchronous method writes a command string followed by a carriage return
        to the transport layer. It is used for commands that require a string value.

        Args:
            cmd (str): The command string to be sent.
            value (str): The string value to be included in the command.

        Example:
            >>> await device_client.write_string_value('set', '80.000')
        """
        logger.debug("Writing string value: %s,%s", cmd, value)
        await self.write(f"{cmd},{value}")

    async def read_response_string(self, cmd: str, timeout : float = DEFAULT_TIMEOUT_SECS) -> str:
        """
        Sends a command to the transport layer and reads the response asynchronously.
        For example, if you write ``cl`` to the device, it will return ``cl,0`` or ``cl,1``
        depending on the current PID mode. That means, this function returns the
        complete string ``cl,0\\r\\n`` or ``cl,1\\r\\n`` including the carriage return and line feed.

        Args:
            cmd (str): The command string to be sent.
            timeout: The timeout for reading the response in seconds.

        Returns:
            str: The response received from the transport layer.

        Example: 
            >>> response = await device_client.read('cl')
            >>> print(response)
            b'cl,1\\r\\n'
        """
        async with self.lock:
            await self._transport.write(cmd + self.frame_delimiter_write)
            return await self._read_raw_message(timeout)
          

    async def read_stripped_response_string(self, cmd: str, timeout : float = DEFAULT_TIMEOUT_SECS) -> str:
        """
        Reads a response string from the device, stripping any leading/trailing whitespace.
        This method is a placeholder and should be implemented based on actual response handling.
        """
        response = await self.read_response_string(cmd, timeout)
        return response.strip("\x01\n\r\x00")
    

    async def read_response_parameters_string(self, cmd: str, timeout : float = DEFAULT_TIMEOUT_SECS) -> str:
        """
        Asynchronously sends a command and retrieves the parameters portion of the response string.

        Args:
            cmd (str): The command string to send.
            timeout (float, optional): The maximum time to wait for a response, in seconds. Defaults to DEFAULT_TIMEOUT_SECS.

        Returns:
            str: The parameters part of the response string (after the first comma), or an empty string if no parameters are present.
        """
        response = await self.read_stripped_response_string(cmd, timeout)
        parts = response.split(',', 1)
        if len(parts) > 1:
            return parts[1]
        else:
            return ""
        

    async def read_cached_response_parameters_tring(self, cmd: str, timeout : float = DEFAULT_TIMEOUT_SECS) -> str:
        """
        Asynchronously reads the response parameters string for a given command, utilizing a cache if enabled.
        If caching is enabled and the command's response is present in the cache, returns the cached response.
        Otherwise, reads the response using `read_response_parameters_string`, caches it if applicable, and returns it.

        Args:
            cmd (str): The command string to send.
            timeout (float, optional): Timeout in seconds for the response. Defaults to DEFAULT_TIMEOUT_SECS.

        Returns:
            str: The parameters part of the response string (after the first comma), or an empty string if no parameters are present.
        """
        if self.CMD_CACHE_ENABLED and cmd in self._cache:
            logger.debug("Read cache hit for command: %s -> %s", cmd, self._cache[cmd])
            return self._cache[cmd]
        
        response = await self.read_response_parameters_string(cmd, timeout)
        if self.CMD_CACHE_ENABLED and cmd in self.CACHEABLE_COMMANDS:
            self._cache[cmd] = response
            logger.debug("Cached value after read: %s -> %s", cmd, response)
        return response
   
   
    async def read_response(self, cmd: str, timeout : float = DEFAULT_TIMEOUT_SECS) -> tuple:
        """
        Asynchronously sends a command to read values and returnes the response as a tuple.
        For example, if you write the command ``set``, it will return ``set,80.000`` if
        the setpoint is 80.000. The response is parsed into a tuple containing the command ``set``
        and a list of parameter strings, in this case ``[80.000]``.

        Args:
            cmd (str): The command string to be sent.

        Returns:
            tuple: A tuple containing the command (str) and a list of parameters (list of str).
        
        Example:
            >>> response = await device_client.read_response('set')
            >>> print(response)
            ('set', ['80.000'])
        """
        response = await self.read_response_string(cmd, timeout)
        return self._parse_response(response)


    async def read_values(self, cmd: str, timeout : float = DEFAULT_TIMEOUT_SECS) -> list[str]:
        """
        Asynchronously sends a command and returns the values as a list of strings.
        For example, if you write the command ``recout,0,0,1``, to read the first data recorder
        value, it will return ``['0', '0', '0.029']`` if the first data recorder value is ``0.029``.
        So it returns a list of 3 strings.

        Args:
            cmd (str): The command string to be sent.

        Returns:
            A list of values (list of str)..

        Example:
            >>> values = await device_client.read_values('recout,0,0,1')
            >>> print(values)
            ['0', '0', '0.029']
        """
        return (await self.read_response(cmd, timeout))[1]
    

    async def read_string_value(self, cmd: str, param_index : int = 0) -> str:
        """
        Asynchronously reads a single string value from device.
        For example, if you write the command ``desc``, the device will return
        the name of the actuator i.e. TRITOR100SG . The response is parsed 
        into a string value.

        Args:
            cmd (str): The command string to be sent.
            param_index (int): Parameter index (default 0) to read from the response.

        Returns:
            str: The value as a string.

        Example:
            >>> await self.read_string_value('desc')
            >>> print(value)
            TRITOR100SG
        """
        if self.CMD_CACHE_ENABLED and cmd in self._cache:
            logger.debug("Read cache hit for command: %s -> %s", cmd, self._cache[cmd])
            return self._cache[cmd]
        

        logger.debug("Reading string value for command: %s, param_index: %d", cmd, param_index)
        value = (await self.read_values(cmd))[param_index]
        if self.CMD_CACHE_ENABLED and cmd in self.CACHEABLE_COMMANDS:
            self._cache[cmd] = value
            logger.debug("Cached value after read: %s -> %s", cmd, value)
        return value


    async def read_float_value(self, cmd: str, param_index : int = 0) -> float:
        """
        Asynchronously reads a single float value from device.
        For example, if you write the command ``set``, to read the current setpoint,
        it will return ``80.000`` if the setpoint is 80.000. The response is parsed into a
        float value. Use this function for command that returns a single floating point value.

        Args:
            cmd (str): The command string to be sent.
            param_index (int): Parameter index (default 0) to read from the response.

        Returns:
            float: The value as a floating-point number.

        Example:
            >>> value = await device_client.read_float_value('set')
            >>> print(value)
            80.000
        """
        return float(await self.read_string_value(cmd, param_index))


    async def read_int_value(self, cmd: str, param_index : int = 0) -> int:
        """
        Asynchronously reads a single float value from device.
        For example, if you write ``cl`` to the device, the response will be ``0`` or ``1``
        depending on the current PID mode. The response is parsed into an integer value.

        Args:
            cmd (str): The command string to be sent.
            param_index (int): Parameter index (default 0) to read from the response

        Returns:
            float: The value as a floating-point number.

        Example:
            >>> value = await device_client.read_int_value('cl')
            >>> print(value)
            1
        """
        return int(await self.read_string_value(cmd, param_index))


    async def close(self):
        """
        Asynchronously closes the transport connection.

        This method ensures that the transport layer is properly closed,
        releasing any resources associated with it.
        """
        await self._transport.close()

    async def get_device_type(self) -> str:
        """
        Retrieves the type of the device.
        The device type is the string that is returned if you just press enter after connecting to the device.
        """
        await self._transport.flush_input()  # Ensure no pending input
        await self._transport.write("\r\n")
        response = await self._transport.read_until(b"\n")
        response = response.strip("\x01\n\r\x00<>")
        logger.info("Device type response: %s", response)
        return response
    
    async def check_device_type(self) -> tuple[bool, str]:
        """
        Checks if the device type matches the given device ID.

        Returns:
            bool: True if the device type matches, False otherwise.
        """
        detected_device_type = await self.get_device_type()
        return (detected_device_type == self.DEVICE_ID, detected_device_type)
    
    async def enrich_device_info(self, detected_device : DetectedDevice) -> None :
        """
        Get additional information about the device.

        A derived class should implement this method to enrich the device information in the given
        detected_device object.

        Args:
            detected_device (DetectedDevice): The detected device object to enrich with additional information.
        """
        pass

    @property
    def device_info(self) -> DeviceInfo:
        """
        Returns detailed information about the connected device.

        This property provides a DeviceInfo object that includes
        the device's identifier and transport metadata. It requires
        that the transport layer is initialized and connected.

        Raises:
            RuntimeError: If the transport is not initialized or the device
                        is not connected.

        Returns:
            DeviceInfo: An object containing the device ID and transport info.
        """
        if self._transport is None:
            raise RuntimeError("Cannot access device_info: transport is not initialized.")
        
        return DeviceInfo(
            device_id=self.DEVICE_ID,
            transport_info=self._transport.get_info()
        )
    
    def clear_cmd_cache(self):
        """
        Clears the cache of previously issued commands.
        """
        self._cache.clear()
        logger.debug("Command cache cleared.")

    @classmethod
    def help(cls, cmd: str | None = None) -> str:
        """
        Returns help information for a specific command or all commands if no command is specified.

        Args:
            cmd (str, optional): The command to get help for. If None, returns help for all commands.

        Returns:
            str: Help information for the specified command or all commands.
        """
        if cmd is None:
            return "\n".join(f"{cmd}: {help}" for cmd, help in cls._help_dict.items())
        else:
            return cls._help_dict.get(cmd, f"No help available for command '{cmd}'.")
        
    @classmethod
    def help_dict(cls):
        """
        Returns the class-level help dictionary with a list of all commands and their descriptions.
        """
        return cls._help_dict
    

PiezoDeviceType = TypeVar("PiezoDeviceType", bound=PiezoDeviceBase)

   
DEVICE_MODEL_REGISTRY: Dict[str, Type[PiezoDeviceBase]] = {}


