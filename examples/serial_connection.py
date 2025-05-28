import asyncio
from nv200.nv200_device import NV200Device
from nv200.transport_protocol import SerialProtocol


async def serial_port_auto_detect():
    """
    Automatically detects and connects to a device over a serial port.

    This asynchronous function initializes a serial transport protocol, creates a device client,
    and attempts to connect to the device. Upon successful connection, it prints the serial port
    used for the connection and then closes the client.
    """
    transport = SerialProtocol()
    client = NV200Device(transport)
    await client.connect()
    print(f"Connected to device on serial port: {transport.port}")
    await client.close()


if __name__ == "__main__":
    asyncio.run(serial_port_auto_detect())
