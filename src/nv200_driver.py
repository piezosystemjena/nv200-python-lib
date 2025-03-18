# -*- coding: utf-8 -*-
"""
Ethernet_simple.py 23.12.2021 Rev0

This example script shows the basic way to communicate with the NV200D/NET via 
Telnet with known IP address. First the connection is established and it is checked if the 
controller reacts. Then a closed loop step to a position of 10 µm (or 10mrad 
for tilting actuators) is executed and after one second of waiting time the
reached position of the actuator is queried and displayed.

Expected output:
NV200/D_NET>
meas,9.942

Note that the value may vary due to sensor noise and controller performance

"""

import asyncio, telnetlib3
import aioserial
import lantronix_device_discovery_async as ldd
from abc import ABC, abstractmethod

# Abstract Base Class for Transport Protocols
class TransportProtocol(ABC):
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
    def __init__(self, host: str = None, port: int = 23, MAC: str = None):
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

    async def connect(self):
        self.serial = aioserial.AioSerial(port=self.port, xonxoff=self.xonxoff, baudrate=self.baudrate)

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



IP='192.168.10.188'     # NV200D/NET IP address, has to be adjusted to your address
port=23                 # Telnet Port (default: 23)

async def telnet_client():
    reader, writer = await telnetlib3.open_connection(IP, port)
    writer.write('\r')
    response = await reader.readuntil(b'\n')
    print(f"Server response: {response}")
    writer.write('modsrc,0\r')   # Set setpoint source to Telnet/USB input  
    writer.write('cl,1\r')       # Set controller to closed loop mode
    writer.write('set,40\r')     # Set setpoint to 10 µm (or mrad for tilting actuators)
    await asyncio.sleep(0.1)
    writer.write('meas\r')       # Query position measurement
    print("waiting...")
    response = await reader.readuntil(b'\n')
    print(f"Server response: {response}")
    writer.close()


async def serial_client():
    serial = aioserial.AioSerial(port='COM3', xonxoff=True, baudrate=115200)
    await serial.write_async(b'\r')
    response = await serial.readline_async()
    print(f"Server response: {response}")
    await serial.write_async(b'modsrc,0\r')   # Set setpoint source to Telnet/USB input  
    await serial.write_async(b'cl,1\r')       # Set controller to closed loop mode
    await serial.write_async(b'set,40\r')     # Set setpoint to 10 µm (or mrad for tilting actuators)
    await asyncio.sleep(0.1)
    await serial.write_async(b'meas\r')       # Query position measurement
    print("waiting...")
    response = await serial.readline_async()
    print(f"Server response: {response}")
    serial.close()


async def client_telnet():
    #transport = TelnetTransport(MAC="00:80:A3:79:C6:18")
    transport = TelnetTransport()
    client = DeviceClient(transport)
    await client.connect()

    response = await client.read('')
    print(f"Server response: {response}")    
    await client.write('modsrc,0')
    await client.write('cl,1')
    await client.write('set,40')
    await asyncio.sleep(0.1)
    response = await client.read('meas')
    print(f"Server response: {response}")
    await client.close()


async def client_serial():
    transport = SerialTransport()
    client = DeviceClient(transport)
    await client.connect()

    response = await client.read('')
    print(f"Server response: {response}")    
    await client.write('modsrc,0')
    await client.write('cl,1')
    await client.write('set,40')
    await asyncio.sleep(0.1)
    response = await client.read('meas')
    print(f"Server response: {response}")
    await client.close()


#asyncio.run(telnet_client())
#asyncio.run(serial_client())
asyncio.run(client_telnet())
asyncio.run(client_serial())


# IP='192.168.10.188'     # NV200D/NET IP address, has to be adjusted to your address
# port=23                 # Telnet Port (default: 23)
# timeout=0.25            # Timeout for reading device answers

# NV200 = telnetlib3.Telnet(IP, port)  # open Telnet connection to NV200D/NET

# NV200.write(b'\r')   # Query device prompt response 
# print(NV200.read_until(b'\n',timeout).decode(),end='') # Read and print device prompt response

# NV200.write(b'modsrc,0\r')   # Set setpoint source to Telnet/USB input
# NV200.write(b'cl,1\r')       # Set controller to closed loop mode
# NV200.write(b'set,40\r')     # Set setpoint to 10 µm (or mrad for tilting actuators)
# time.sleep(0.1)                               # Wait for actuator to change position
# NV200.write(b'meas\r')       # Query position measurement
# print(NV200.read_until(b'\n',timeout).decode(),end='') # Read and print device answer to position measurement query

# NV200.close()   # close Telnet connection to NV200D/NET