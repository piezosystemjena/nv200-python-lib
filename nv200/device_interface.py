import asyncio
from enum import Enum, IntFlag
from transport_protocols import TelnetProtocol, SerialProtocol, TransportProtocol


class PidLoopMode(Enum):
    """
    PidLoopMode is an enumeration that defines the modes of operation for a PID control loop.
    """
    OPEN_LOOP = 0
    CLOSED_LOOP = 1

class ErrorCode(Enum):
    """
    ErrorCode(Enum):
        An enumeration representing various error codes and their corresponding descriptions.
    """
    ERROR_NOT_SPECIFIED = 1
    UNKNOWN_COMMAND = 2
    PARAMETER_MISSING = 3
    ADMISSIBLE_PARAMETER_RANGE_EXCEEDED = 4
    COMMAND_PARAMETER_COUNT_EXCEEDED = 5
    PARAMETER_LOCKED_OR_READ_ONLY = 6
    UNDERLOAD = 7
    OVERLOAD = 8
    PARAMETER_TOO_LOW = 9
    PARAMETER_TOO_HIGH = 10

    @classmethod
    def from_value(cls, value : int):
        """Convert an integer into an ErrorCode enum member."""
        if value in cls._value2member_map_:
            return cls(value)
        else:
            return cls.ERROR_NOT_SPECIFIED  # Default error if value is invalid

    # Method to get the error description based on the error code
    @classmethod
    def get_description(cls, error_code) -> str:
        """
        Retrieves a human-readable description for a given error code.

        Args:
            error_code (int): The error code for which the description is requested.

        Returns:
            str: A string describing the error associated with the provided error code.
                 If the error code is not recognized, "Unknown error" is returned.
        """
        descriptions = {
            cls.ERROR_NOT_SPECIFIED: "Error not specified",
            cls.UNKNOWN_COMMAND: "Unknown command",
            cls.PARAMETER_MISSING: "Parameter missing",
            cls.ADMISSIBLE_PARAMETER_RANGE_EXCEEDED: "Admissible parameter range exceeded",
            cls.COMMAND_PARAMETER_COUNT_EXCEEDED: "Command's parameter count exceeded",
            cls.PARAMETER_LOCKED_OR_READ_ONLY: "Parameter is locked or read only",
            cls.UNDERLOAD: "Underload",
            cls.OVERLOAD: "Overload",
            cls.PARAMETER_TOO_LOW: "Parameter too low",
            cls.PARAMETER_TOO_HIGH: "Parameter too high"
        }
        return descriptions.get(error_code, "Unknown error")
    
class StatusFlags(IntFlag):
    """
    Enum representing the individual status flags within a 16-bit status register.
    """
    ACTUATOR_CONNECTED = 1 << 0
    SENSOR_TYPE_0 = 1 << 1
    SENSOR_TYPE_1 = 1 << 2
    CLOSED_LOOP_MODE = 1 << 3
    LOW_PASS_FILTER_ON = 1 << 4
    NOTCH_FILTER_ON = 1 << 5
    SIGNAL_PROCESSING_ACTIVE = 1 << 7
    AMPLIFIER_CHANNELS_BRIDGED = 1 << 8
    TEMPERATURE_TOO_HIGH = 1 << 10
    ACTUATOR_ERROR = 1 << 11
    HARDWARE_ERROR = 1 << 12
    I2C_ERROR = 1 << 13
    LOWER_CONTROL_LIMIT_REACHED = 1 << 14
    UPPER_CONTROL_LIMIT_REACHED = 1 << 15

    @staticmethod
    def get_sensor_type(value):
        """
        Determines the type of sensor based on the sensor bits in the status register.
        
        :param value: The 16-bit status register value.
        :return: A string describing the sensor type.
        """
        sensor_bits = (value & (StatusFlags.SENSOR_TYPE_0 | StatusFlags.SENSOR_TYPE_1)) >> 1
        sensor_types = {
            0b00: "No position sensor",
            0b01: "Strain gauge sensor",
            0b10: "Capacitive sensor"
        }
        return sensor_types.get(sensor_bits, "Unknown")

class StatusRegister:
    """
    A class representing the 16-bit status register of an actuator or amplifier.
    """
    def __init__(self, value: int):
        """
        Initializes the StatusRegister with a given 16-bit value.
        
        :param value: The 16-bit status register value.
        """
        self.flags = StatusFlags(value)
        self.value = value

    def has_flag(self, flag: StatusFlags):
        """
        Checks if a given status flag is set in the register.
        
        :param flag: A StatusFlags enum value to check.
        :return: True if the flag is set, False otherwise.
        """
        return bool(self.flags & flag)

    def __repr__(self):
        """
        Provides a string representation of the status register with human-readable information.
        
        :return: A formatted string showing the status register details.
        """
        return (f"StatusRegister(value={self.value:#06x}):\n"
                f"\tActuator Connected={self.has_flag(StatusFlags.ACTUATOR_CONNECTED)}\n"
                f"\tSensor={StatusFlags.get_sensor_type(self.value)}\n"
                f"\tClosed Loop Mode={self.has_flag(StatusFlags.CLOSED_LOOP_MODE)}\n"
                f"\tLow Pass Filter={self.has_flag(StatusFlags.LOW_PASS_FILTER_ON)}\n"
                f"\tNotch Filter={self.has_flag(StatusFlags.NOTCH_FILTER_ON)}\n"
                f"\tSignal Processing={self.has_flag(StatusFlags.SIGNAL_PROCESSING_ACTIVE)}\n"
                f"\tBridged Amplifier={self.has_flag(StatusFlags.AMPLIFIER_CHANNELS_BRIDGED)}\n"
                f"\tTemp High={self.has_flag(StatusFlags.TEMPERATURE_TOO_HIGH)}\n"
                f"\tActuator Error={self.has_flag(StatusFlags.ACTUATOR_ERROR)}\n"
                f"\tHardware Error={self.has_flag(StatusFlags.HARDWARE_ERROR)}\n"
                f"\tI2C Error={self.has_flag(StatusFlags.I2C_ERROR)}\n"
                f"\tLower Limit Reached={self.has_flag(StatusFlags.LOWER_CONTROL_LIMIT_REACHED)}\n"
                f"\tUpper Limit Reached={self.has_flag(StatusFlags.UPPER_CONTROL_LIMIT_REACHED)}")


class DeviceError(Exception):
    """
    Custom exception class for handling device-related errors.

    Attributes:
        error_code (ErrorCode): The error code associated with the exception.
        description (str): A human-readable description of the error.

    Args:
        error_code (ErrorCode): An instance of the ErrorCode enum representing the error.

    Raises:
        ValueError: If the provided error_code is not a valid instance of the ErrorCode enum.
    """
    def __init__(self, error_code : ErrorCode):
        self.error_code = error_code
        self.description = ErrorCode.get_description(error_code)
        # Call the base class constructor with the formatted error message
        super().__init__(f"Error {self.error_code.value}: {self.description}")


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
            response = await asyncio.wait_for(self._transport.read_response(), timeout=0.1)
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


    async def read_float_value(self, cmd: str) -> float:
        """
        Asynchronously reads a single float value from device

        Args:
            cmd (str): The command string to be sent.

        Returns:
            float: The value as a floating-point number.
        """
        return float((await self.read_values(cmd))[0])


    async def read_int_value(self, cmd: str) -> int:
        """
        Asynchronously reads a single float value from device

        Args:
            cmd (str): The command string to be sent.

        Returns:
            float: The value as a floating-point number.
        """
        return int((await self.read_values(cmd))[0])


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
