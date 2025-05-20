"""
Provides classes and enumerations for communicating with and interpreting responses from NV200 devices.

This module includes an asynchronous client for issuing commands and parsing responses
from NV200 devices over supported transport protocols (e.g., serial, Telnet).

Classes:
    - :class:`.DeviceClient`: High-level async client for device communication.
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
    DetectedDevice
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
        

    async def connect(self, auto_adjust_comm_params: bool = True):
        """
        Establishes a connection using the transport layer.

        This asynchronous method initiates the connection process by calling
        the `connect` method of the transport instance.

        Raises:
            Exception: If the connection fails, an exception may be raised
                       depending on the implementation of the transport layer.
        """
        await self._transport.connect(auto_adjust_comm_params)

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
    

    async def read_string_value(self, cmd: str, param_index : int = 0) -> str:
        """
        Asynchronously reads a single string value from device

        Args:
            cmd (str): The command string to be sent.
            param_index (int): Parameter index (default 0) to read from the response.

        Returns:
            str: The value as a string.

        Example:

            >>> await self.read_string_value('desc')
        """
        return (await self.read_values(cmd))[param_index]


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

    async def move(self, target: float):
        """
        Moves the device to the specified target position or voltage.
        The target is interpreted as a position in closed loop or a voltage in open loop.
        """
        await self.set_setpoint(target)

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
    
    async def get_actuator_name(self) -> str:
        """
        Retrieves the name of the actuator that is connected to the NV200 device.
        """
        return await self.read_string_value('desc')
    
    async def get_actuator_serial_number(self) -> str:
        """
        Retrieves the serial number of the actuator that is connected to the NV200 device.
        """
        return await self.read_string_value('acserno')
    
    async def get_actuator_description(self) -> str:
        """
        Retrieves the description of the actuator that is connected to the NV200 device.
        The description consists of the actuator type and the serial number.
        For example: "TRITOR100SG, #85533"
        """
        name = await self.get_actuator_name()
        serial_number = await self.get_actuator_serial_number()   
        return f"{name} #{serial_number}"
    
    async def get_device_type(self) -> str:
        """
        Retrieves the type of the device.
        The device type is the string that is returned if you just press enter after connecting to the device.
        """
        await self._transport.write("\r\n")
        response = await self._read_response()
        return self._parse_response(response)[0]
    
    async def get_slew_rate(self) -> float:
        """
        Retrieves the slew rate of the device.
        The slew rate is the maximum speed at which the device can move.
        """
        return await self.read_float_value('sr')
    
    async def set_slew_rate(self, slew_rate: float):
        """
        Sets the slew rate of the device.
        0.0000008 ... 2000.0 %ms⁄ (2000 = disabled)
        """
        await self.write(f"sr,{slew_rate}")

    async def enable_setpoint_lowpass_filter(self, enable: bool):
        """
        Enables the low-pass filter for the setpoint.
        """
        await self.write(f"setlpon,{int(enable)}")

    async def is_setpoint_lowpass_filter_enabled(self) -> bool:
        """
        Checks if the low-pass filter for the setpoint is enabled.
        """
        return await self.read_int_value('setlpon') == 1
    
    async def set_setpoint_lowpass_filter_cutoff_freq(self, frequency: int):
        """
        Sets the cutoff frequency of the low-pass filter for the setpoint from 1..10000 Hz.
        """
        await self.write(f"setlpf,{frequency}")

    async def get_setpoint_lowpass_filter_cutoff_freq(self) -> int:
        """
        Retrieves the cutoff frequency of the low-pass filter for the setpoint.
        """
        return await self.read_int_value('setlpf')


def create_device_client(detected_device: DetectedDevice) -> DeviceClient:
    """
    Factory function to create a DeviceClient with the right transport protocol 
    from a DetectedDevice.
    This function determines the appropriate transport protocol
    based on the detected device type (e.g., serial or telnet) and returns a 
    properly configured DeviceClient instance.
    """
    if detected_device.transport == 'telnet':
        transport = TelnetProtocol(host = detected_device.identifier)
    elif detected_device.transport == 'serial':
        transport = SerialProtocol(port = detected_device.identifier)
    else:
        raise ValueError(f"Unsupported dtransport type: {detected_device.transport}")
    
    # Return a DeviceClient initialized with the correct transport protocol
    return DeviceClient(transport)