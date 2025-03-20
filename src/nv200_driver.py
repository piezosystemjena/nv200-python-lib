import asyncio
import telnetlib3
from abc import ABC, abstractmethod
import aioserial
import serial.tools.list_ports
import lantronix_device_discovery_async as ldd
from enum import Enum


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


class TransportProtocol(ABC):
    """
    Abstract base class representing a transport protocol interface for a device.
    """
    @abstractmethod
    async def connect(self):
        """
        Establishes an asynchronous connection to the NV200 device.

        This method is intended to handle the initialization of a connection
        to the NV200 device. The implementation should include the necessary
        steps to ensure the connection is successfully established.

        Raises:
            Exception: If the connection fails or encounters an error.
        """

    @abstractmethod
    async def read_response(self) -> str:
        """
        Asynchronously reads and returns a response as a string.

        Returns:
            str: The response read from the source.
        """

    @abstractmethod
    async def write(self, cmd: str):
        """
        Sends a command to the NV200 device asynchronously.

        Args:
            cmd (str): The command string to be sent to the device.

        Raises:
            Exception: If there is an error while sending the command.
        """

    @abstractmethod
    async def close(self):
        """
        Asynchronously closes the connection or resource associated with this instance.

        This method should be used to release any resources or connections
        that were opened during the lifetime of the instance. Ensure that this
        method is called to avoid resource leaks.

        Raises:
            Exception: If an error occurs while attempting to close the resource.
        """

    async def detect_device(self) -> bool:
        """
        Detects if the connected device is an NV200.

        This asynchronous method sends a command to the device and checks the response
        to determine if the device is an NV200. The detection is based on whether the
        response starts with the byte sequence "NV200".

        Returns:
            bool: True if the device is detected as an NV200, False otherwise.
        """
        await self.write('\r')
        response = await self.read_response()
        return response.startswith(b"NV200")



class TelnetTransport(TransportProtocol):
    """
    TelnetTransport is a class that implements a transport protocol for communicating
    with piezosystem devices over Telnet. It provides methods to establish a connection,
    send commands, read responses, and close the connection.
    """
    __host : str
    __MAC : str
    __port : int
    
    def __init__(self, host: str = None, port: int = 23, MAC: str = None):
        """
        Initializes thetransport protocol.

        Args:
            host (str, optional): The hostname or IP address of the NV200 device. Defaults to None.
            port (int, optional): The port number to connect to. Defaults to 23.
            MAC (str, optional): The MAC address of the NV200 device. Defaults to None.
        """
        self.__host = host
        self.__port = port
        self.__MAC = MAC
        self.__reader = None
        self.__writer = None

    async def connect(self):
        """
        Establishes a connection to a Lantronix device.

        This asynchronous method attempts to connect to a Lantronix device using
        either the provided MAC address or by discovering devices on the network.

        - If `self.host` is `None` and `self.MAC` is provided, it discovers the
          device's IP address using the MAC address.
        - If both `self.host` and `self.MAC` are `None`, it discovers all available
          Lantronix devices on the network and selects the first one.

        Once the device's IP address is determined, it establishes a Telnet
        connection to the device using the specified host and port.

        Raises:
            RuntimeError: If no devices are found during discovery.

        Returns:
            None
        """
        if self.__host is None and self.__MAC is not None:
            self.__host = await ldd.discover_lantronix_device(self.__MAC)
            if self.__host is None:
                raise RuntimeError(f"Device with MAC address {self.__MAC} not found")
        elif self.__host is None and self.__MAC is None:
            devices = await ldd.discover_lantronix_devices()
            if not devices:
                raise RuntimeError("No devices found")
            self.__host = devices[0]['IP']
            self.__MAC = devices[0]['MAC']
        self.__reader, self.__writer = await telnetlib3.open_connection(self.__host, self.__port)
    
    async def write(self, cmd: str):
        self.__writer.write(cmd)
        
    async def read_response(self) -> str:
        return await self.__reader.readuntil(b'\n')

    async def close(self):
        if self.__writer:
            self.__writer.close()
            self.__reader.close()

    @property
    def host(self) -> str:
        """
        Returns the host address.
        """
        return self.__host
    
    @property
    def MAC(self) -> str:
        """
        Returns the MAC address.
        """
        return self.__MAC



class SerialTransport(TransportProtocol):
    """
    A class to handle serial communication with an NV200 device using the AioSerial library.
    Attributes:
        port (str): The serial port to connect to. Defaults to None. If port is None, the class
        will try to auto detect rthe port.
        xonxoff (bool): Whether to enable software flow control. Defaults to True.
        baudrate (int): The baud rate for the serial connection. Defaults to 115200.
        serial (AioSerial): The AioSerial instance for asynchronous serial communication.
    """
    __port : str
    __xonxoff : bool
    __baudrate : int
    
    def __init__(self, port : str = None, xonxoff : bool = True, baudrate : int = 115200):
        """
        Initializes the NV200 driver with the specified serial port settings.

        Args:
            port (str, optional): The serial port to connect to. Defaults to None.
            If port is None, the class will try to auto detect rthe port.
            xonxoff (bool, optional): Enables or disables software flow control (XON/XOFF). Defaults to True.
            baudrate (int, optional): The baud rate for the serial connection. Defaults to 115200.
        """
        self.__serial = None
        self.__port = port
        self.__xonxoff = xonxoff
        self.__baudrate = baudrate


    async def detect_port(self):
        """
        Asynchronously detects and configures the serial port for the NV200 device.

        This method scans through all available serial ports to find one with a 
        manufacturer matching "FTDI". If such a port is found, it attempts to 
        communicate with the device to verify if it is an NV200 device. If the 
        device is successfully detected, the port is configured and returned.

        Returns:
            str: The device name of the detected port if successful, otherwise None.

        Raises:
            Any exceptions raised during serial communication or port configuration 
            are not explicitly handled and will propagate to the caller.
        """
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.manufacturer != "FTDI":
                continue
            self.__serial.close()
            self.__serial.port = port.device
            self.__serial.open()
            if await self.detect_device():
                return port.device
            else:
                self.__serial.close()
        return None

    async def connect(self):
        """
        Establishes an asynchronous connection to the NV200 device using the specified serial port settings.

        This method initializes the serial connection with the given port, baud rate, and flow control settings.
        If the port is not specified, it attempts to automatically detect the NV200 device's port. If the device
        cannot be found, a RuntimeError is raised.

        Raises:
            RuntimeError: If the NV200 device cannot be detected or connected to.
        """
        self.__serial = aioserial.AioSerial(port=self.__port, xonxoff=self.__xonxoff, baudrate=self.__baudrate)
        if self.__port is None:
            self.__port = await self.detect_port()
        if self.__port is None:
            raise RuntimeError("NV200 device not found")


    async def write(self, cmd: str):
        await self.__serial.write_async(cmd.encode('utf-8'))

    async def read_response(self) -> str:
        return await self.__serial.readline_async()

    async def close(self):
        if self.__serial:
            self.__serial.close()

    @property
    def port(self) -> str:
        """
        Returns the serial port the device is connected to
        """
        return self.__port


class DeviceClient:
    """
    A client for communicating with a NV200 device using a specified transport protocol.
    Attributes:
        transport (TransportProtocol): The transport protocol used for communication.
    """
    def __init__(self, transport: TransportProtocol):
        self.transport = transport

    async def _read_response(self, timeout_param : float = 0.4) -> str:
        """
        Asynchronously reads a response from the transport layer with a specified timeout.
        """
        return await asyncio.wait_for(self.transport.read_response(), timeout=timeout_param)
        

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
        await self.transport.connect()

    async def write(self, cmd: str):
        """
        Sends a command to the transport layer.

        This asynchronous method writes a command string followed by a carriage return
        ("\r") to the transport layer.

        Args:
            cmd (str): The command string to be sent. No carriage return is needed.
        """
        await self.transport.write(cmd + "\r")
        try:
            response = await asyncio.wait_for(self.transport.read_response(), timeout=0.1)
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
        await self.transport.write(cmd + "\r")
        return await self._read_response()

    async def close(self):
        """
        Asynchronously closes the transport connection.

        This method ensures that the transport layer is properly closed,
        releasing any resources associated with it.
        """
        await self.transport.close()
        
    async def set_pid_mode(self, mode: PidLoopMode):
        """Sets the PID mode of the device to either open loop or closed loop."""
        await self.write(f"cl,{mode.value}")

    async def get_pid_mode(self) -> PidLoopMode:
        """Retrieves the current PID mode of the device."""
        response = await self.read('cl')
        parameters = self._parse_response(response)[1]
        return PidLoopMode(int(parameters[0]))
    
    async def set_setpoint(self, setpoint: float):
        """Sets the setpoint value for the device."""
        await self.write(f"set,{setpoint}")

    async def get_setpoint(self) -> float:
        """Retrieves the current setpoint of the device."""
        response = await self.read('set')
        parameters = self._parse_response(response)[1]
        return float(parameters[0])
    
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
        response = await self.read('meas')
        parameters = self._parse_response(response)[1]
        return float(parameters[0])


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
    transport = TelnetTransport(MAC="00:80:A3:79:C6:18")
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
    transport = SerialTransport()
    client = DeviceClient(transport)
    await client.connect()
    print(f"Connected to device on serial port: {transport.port}")
    await run_tests(client)


if __name__ == "__main__":
    asyncio.run(client_telnet_test())
    #asyncio.run(client_serial_test())
