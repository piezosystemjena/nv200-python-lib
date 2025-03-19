import asyncio, telnetlib3
import aioserial
import serial.tools.list_ports
import lantronix_device_discovery_async as ldd
from abc import ABC, abstractmethod

# Abstract Base Class for Transport Protocols
class TransportProtocol(ABC):
    """
    Abstract base class representing a transport protocol interface for a device.
    """
    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def write(self, cmd: str):
        pass

    @abstractmethod
    async def read(self, cmd: str) -> str:
        pass

    @abstractmethod
    async def close(self):
        pass


# Telnet Transport Implementation
class TelnetTransport(TransportProtocol):
    """
    TelnetTransport is a class that implements a transport protocol for communicating
    with piezosystem devices over Telnet. It provides methods to establish a connection,
    send commands, read responses, and close the connection.
    """
    
    def __init__(self, host: str = None, port: int = 23, MAC: str = None):
        """
        Initializes thetransport protocol.

        Args:
            host (str, optional): The hostname or IP address of the NV200 device. Defaults to None.
            port (int, optional): The port number to connect to. Defaults to 23.
            MAC (str, optional): The MAC address of the NV200 device. Defaults to None.
        """
        self.host = host
        self.port = port
        self.MAC = MAC
        self.reader = None
        self.writer = None

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
        if self.host is None and self.MAC is not None:
            self.host = await ldd.discover_lantronix_device(self.MAC)
            if self.host is None:
                raise RuntimeError(f"Device with MAC address {self.MAC} not found")
        elif self.host is None and self.MAC is None:
            devices = await ldd.discover_lantronix_devices()
            if not devices:
                raise RuntimeError("No devices found")
            self.host = devices[0]['IP']
            self.MAC = devices[0]['MAC']
        self.reader, self.writer = await telnetlib3.open_connection(self.host, self.port)

    async def write(self, cmd: str):
        self.writer.write(cmd)

    async def read(self, cmd: str) -> str:
        self.writer.write(cmd)
        return await self.reader.readuntil(b'\n')

    async def close(self):
        if self.writer:
            self.writer.close()
            self.reader.close()

# Serial Transport Implementation
class SerialTransport(TransportProtocol):
    def __init__(self, port = None, xonxoff = True, baudrate = 115200):
        self.serial = None
        self.port = port
        self.xonxoff = xonxoff
        self.baudrate = baudrate

    async def detect_port(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.manufacturer != "FTDI":
                continue
            self.serial.close()
            self.serial.port = port.device
            self.serial.open()
            response = await self.read('\r')
            if response.startswith(b"NV200"):
                self.port = port.device
                return self.port
            else:
              self.serial.close()
            return None

    async def connect(self):
        self.serial = aioserial.AioSerial(port=self.port, xonxoff=self.xonxoff, baudrate=self.baudrate)
        if self.port is None:
            self.port = await self.detect_port()
        if self.port is None:
            raise RuntimeError("NV200 device not found")


    async def write(self, cmd: str):
        await self.serial.write_async(cmd.encode('utf-8'))

    async def read(self, cmd: str) -> str:
        await self.serial.write_async(cmd.encode('utf-8'))
        return await self.serial.readline_async()

    async def close(self):
        if self.serial:
            self.serial.close()


class DeviceClient:
    def __init__(self, transport: TransportProtocol):
        self.transport = transport

    async def connect(self):
        await self.transport.connect()

    async def write(self, cmd: str):
        await self.transport.write(cmd + "\r")

    async def read(self, cmd: str) -> str:
        return await self.transport.read(cmd + "\r")

    async def close(self):
        await self.transport.close()


async def client_telnet():
    #transport = TelnetTransport(MAC="00:80:A3:79:C6:18")
    transport = TelnetTransport()
    client = DeviceClient(transport)
    await client.connect()

    response = await client.read('')
    print(f"Telnet - Server response: {response}")    
    await client.write('modsrc,0')
    await client.write('cl,1')
    await client.write('set,40')
    await asyncio.sleep(0.1)
    response = await client.read('meas')
    print(f"Telnet - Server response: {response}")
    await client.close()


async def client_serial():
    transport = SerialTransport()
    client = DeviceClient(transport)
    await client.connect()

    response = await client.read('')
    print(f"Serial - Server response: {response}")    
    await client.write('modsrc,0')
    await client.write('cl,1')
    await client.write('set,40')
    await asyncio.sleep(0.1)
    response = await client.read('meas')
    print(f"Serial - Server response: {response}")
    await client.close()


asyncio.run(client_telnet())
asyncio.run(client_serial())
