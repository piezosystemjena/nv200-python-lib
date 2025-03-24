import asyncio
from enum import Enum
from transport_protocols import TelnetProtocol, SerialProtocol, TransportProtocol


class PidLoopMode(Enum):
    """
    PidLoopMode is an enumeration that defines the modes of operation for a PID control loop.

    Attributes:
        OPEN_LOOP (int): Represents an open-loop mode where the system operates without feedback.
        CLOSED_LOOP (int): Represents a closed-loop mode where the system operates with feedback.
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
    def get_description(cls, error_code):
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
    def __init__(self, transport: TransportProtocol):
        self._transport = transport

    @property
    def serial_protocol(self) -> SerialProtocol:
        """Returns the transport as SerialProtocol or raises TypeError."""
        if isinstance(self._transport, SerialProtocol):
            return self._transport
        raise TypeError("Transport is not a SerialTransport")

    @property
    def ethernet_protocol(self) -> TelnetProtocol:
        """Returns the transport as TelnetProtocol or raises TypeError."""
        if isinstance(self._transport, TelnetProtocol):
            return self._transport
        raise TypeError("Transport is not a TelnetTransport")

    async def _read_response(self, timeout_param : float = 0.4) -> str:
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
        ("\r") to the transport layer.

        Args:
            cmd (str): The command string to be sent. No carriage return is needed.
        """
        await self._transport.write(cmd + "\r")
        try:
            response = await asyncio.wait_for(self._transport.read_response(), timeout=0.1)
            return self._parse_response(response)
        except asyncio.TimeoutError:
            return None  # Or handle it differently

    async def read(self, cmd: str) -> str:
        """
        Sends a command to the transport layer and reads the response asynchronously.

        Args:
            cmd (str): The command string to be sent.

        Returns:
            str: The response received from the transport layer.
        """
        await self._transport.write(cmd + "\r")
        return await self._read_response()
   
   
    async def read_values(self, cmd: str) -> tuple:
        response = await self.read(cmd)
        return self._parse_response(response)

    
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
        return PidLoopMode(int((await self.read_values('cl'))[1][0]))
    
    async def set_setpoint(self, setpoint: float):
        """Sets the setpoint value for the device."""
        await self.write(f"set,{setpoint}")

    async def get_setpoint(self) -> float:
        """Retrieves the current setpoint of the device."""
        return float((await self.read_values('set'))[1][0])
    
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
        return float((await self.read_values('meas'))[1][0])


async def run_tests(client: DeviceClient):
    response = await client.read('')
    print(f"Server response: {response}")    
    await client.write('modsrc,0')
    await client.write('cl,1')
    await client.write('set,40')
    await asyncio.sleep(0.1)
    response = await client.read('meas')
    print(f"Server response: {response}")
    response = await client.read('cl')
    print(f"Server response: {response}")
    print("Current position:", await client.get_current_position())
    await client.set_pid_mode(PidLoopMode.CLOSED_LOOP)
    await client.set_pid_mode(PidLoopMode.OPEN_LOOP)
    value = await client.get_pid_mode()
    print("PID mode:", value)
    await client.set_setpoint(0)
    setpoint = await client.get_setpoint()
    print("Setpoint:", setpoint)
    print("Current position:", await client.get_current_position())
    await client.close()


async def client_telnet_test():
    """
    Asynchronous function to test a Telnet connection to a device using the `TelnetTransport` 
    and `DeviceClient` classes.
    This function establishes a connection to a device, sends a series of commands, 
    reads responses, and then closes the connection.
    """
    transport = TelnetProtocol(MAC="00:80:A3:79:C6:18")
    #transport = TelnetTransport()
    client = DeviceClient(transport)
    await client.connect()
    print(f"Connected to device with IP: {transport.host}")
    await run_tests(client)



async def client_serial_test():
    """
    Asynchronous function to test serial communication with a device client.
    This function establishes a connection to a device using a serial transport,
    sends a series of commands, and retrieves responses from the device.
    """
    transport = SerialProtocol()
    client = DeviceClient(transport)
    await client.connect()
    print(f"Connected to device on serial port: {transport.port}")
    await run_tests(client)


if __name__ == "__main__":
    asyncio.run(client_telnet_test())
    asyncio.run(client_serial_test())
