"""
Provides classes and enumerations for communicating with and interpreting responses from NV200 devices.

This module includes an asynchronous client for issuing commands and parsing responses
from NV200 devices over supported transport protocols (e.g., serial, Telnet).
It also defines enums for PID loop modes, error codes, status flags, and modulation sources,
as well as utility classes for decoding device status and handling exceptions.

Classes:
    - :class:`.DeviceClient`: High-level async client for device communication.
    - :class:`.StatusRegister`: Parses and interprets the device's 16-bit status register.
    - :class:`.DeviceError`: Exception raised for device-reported error codes.
    - :class:`.PidLoopMode`: PID loop control modes (open/closed).
    - :class:`.ErrorCode`: Device error codes with human-readable descriptions.
    - :class:`.StatusFlags`: Bitmask flags from the device's status register.
    - :class:`.ModulationSource`: Supported sources for setpoint modulation.
"""

import asyncio
from enum import Enum, IntFlag
from nv200.transport_protocols import TelnetProtocol, SerialProtocol, TransportProtocol
from nv200.device_types import (
    PidLoopMode,
    ErrorCode,
    StatusFlags,
    ModulationSource,
    StatusRegister,
    DeviceError,
)



class DeviceClient:
    """
    A client for communicating with a NV200 device using a specified transport protocol.

    Attributes:
        transport (TransportProtocol): The transport protocol used for communication.
    """
    DEFAULT_TIMEOUT_SECS = 0.4
    
    def __init__(self, transport: TransportProtocol):
        self._transport = transport

    @property
    def serial_protocol(self) -> SerialProtocol:
        """
        Returns the transport as SerialProtocol or raises TypeError.
        
        Returns:
            SerialProtocol: The transport instance as SerialProtocol.
        """
        if isinstance(self._transport, SerialProtocol):
            return self._transport
        raise TypeError("Transport is not a SerialTransport")

    @property
    def ethernet_protocol(self) -> TelnetProtocol:
        """Returns the transport as TelnetProtocol or raises TypeError."""
        if isinstance(self._transport, TelnetProtocol):
            return self._transport
        raise TypeError("Transport is not a TelnetTransport")

    async def _read_response(self, timeout_param : float = DEFAULT_TIMEOUT_SECS) -> str:
        """
        Asynchronously reads a response from the transport layer with a specified timeout.
        """
        return await asyncio.wait_for(self._transport.read_response(), timeout=timeout_param)
        

    def _parse_response(self, response_param: bytes) -> tuple:
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
        response = response_param.decode('utf-8')
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
            # Normal response, split the command and parameters
            parts = response.split(',', 1)
            command = parts[0].strip()
            parameters = []
            if len(parts) > 1:
                parameters = [param.strip("\x01\n\r\x00") for param in parts[1].split(',')]
            return command, parameters
        

    async def connect(self):
        """
        Establishes a connection using the transport layer.

        This asynchronous method initiates the connection process by calling
        the `connect` method of the transport instance.

        Raises:
            Exception: If the connection fails, an exception may be raised
                       depending on the implementation of the transport layer.
        """
        await self._transport.connect()

    async def write(self, cmd: str):
        """
        Sends a command to the transport layer.

        This asynchronous method writes a command string followed by a carriage return
        to the transport layer.

        Args:
            cmd (str): The command string to be sent. No carriage return is needed.  
        """
        print(f"Writing command: {cmd}")
        await self._transport.write(cmd + "\r")
        try:
            response = await asyncio.wait_for(self._transport.read_response(), timeout=0.4)
            return self._parse_response(response)
        except asyncio.TimeoutError:
            return None  # Or handle it differently

    async def read(self, cmd: str, timeout : float = DEFAULT_TIMEOUT_SECS) -> str:
        """
        Sends a command to the transport layer and reads the response asynchronously.

        Args:
            cmd (str): The command string to be sent.
            timeout: The timeout for reading the response in seconds.

        Returns:
            str: The response received from the transport layer.
        """
        await self._transport.write(cmd + "\r")
        return await self._read_response(timeout)
   
   
    async def read_response(self, cmd: str, timeout : float = DEFAULT_TIMEOUT_SECS) -> tuple:
        """
        Asynchronously sends a command to read values and parses the response.

        Args:
            cmd (str): The command string to be sent.

        Returns:
            tuple: A tuple containing the command (str) and a list of parameters (list of str)..
        """
        response = await self.read(cmd, timeout)
        return self._parse_response(response)


    async def read_values(self, cmd: str, timeout : float = DEFAULT_TIMEOUT_SECS) -> list[str]:
        """
        Asynchronously sends a command and returns the values as a list of strings

        Args:
            cmd (str): The command string to be sent.

        Returns:
            A list of values (list of str)..
        """
        return (await self.read_response(cmd, timeout))[1]


    async def read_float_value(self, cmd: str, param_index : int = 0) -> float:
        """
        Asynchronously reads a single float value from device

        Args:
            cmd (str): The command string to be sent.
            param_index (int): Parameter index (default 0) to read from the response.

        Returns:
            float: The value as a floating-point number.
        """
        return float((await self.read_values(cmd))[param_index])


    async def read_int_value(self, cmd: str, param_index : int = 0) -> int:
        """
        Asynchronously reads a single float value from device

        Args:
            cmd (str): The command string to be sent.
            param_index (int): Parameter index (default 0) to read from the response

        Returns:
            float: The value as a floating-point number.
        """
        return int((await self.read_values(cmd))[param_index])


    async def close(self):
        """
        Asynchronously closes the transport connection.

        This method ensures that the transport layer is properly closed,
        releasing any resources associated with it.
        """
        await self._transport.close()
        
    async def set_pid_mode(self, mode: PidLoopMode):
        """Sets the PID mode of the device to either open loop or closed loop."""
        await self.write(f"cl,{mode.value}")

    async def get_pid_mode(self) -> PidLoopMode:
        """Retrieves the current PID mode of the device."""
        return PidLoopMode(await self.read_int_value('cl'))
    
    async def set_modulation_source(self, source: ModulationSource):
        """Sets the setpoint modulation source."""
        await self.write(f"modsrc,{source.value}")

    async def get_modulation_source(self) -> ModulationSource:
        """Retrieves the current setpoint modulation source."""
        return ModulationSource(await self.read_int_value('modsrc'))
    
    async def set_setpoint(self, setpoint: float):
        """Sets the setpoint value for the device."""
        await self.write(f"set,{setpoint}")

    async def get_setpoint(self) -> float:
        """Retrieves the current setpoint of the device."""
        return await self.read_float_value('set')
    
    async def move_to_position(self, position: float):
        """Moves the device to the specified position in closed loop"""
        await self.set_pid_mode(PidLoopMode.CLOSED_LOOP)
        await self.set_setpoint(position)

    async def move_to_voltage(self, voltage: float):
        """Moves the device to the specified voltage in open loop"""
        await self.set_pid_mode(PidLoopMode.OPEN_LOOP)
        await self.set_setpoint(voltage)

    async def get_current_position(self) -> float:
        """
        Retrieves the current position of the device.
        For actuators with sensor: Position in actuator units (μm or mrad)
        For actuators without sensor: Piezo voltage in V
        """
        return await self.read_float_value('meas')

    async def get_heat_sink_temperature(self) -> float:
        """
        Retrieves the heat sink temperature in degrees Celsius.
        """
        return await self.read_float_value('temp')

    async def get_status_register(self) -> StatusRegister:
        """
        Retrieves the status register of the device.
        """
        return StatusRegister(await self.read_int_value('stat'))

    async def is_status_flag_set(self, flag: StatusFlags) -> bool:
        """
        Checks if a specific status flag is set in the status register.
        """
        status_reg = await self.get_status_register()
        return status_reg.has_flag(flag)
