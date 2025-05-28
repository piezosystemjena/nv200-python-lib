import asyncio
from nv200.nv200_device import NV200Device
from nv200.transport_protocol import TelnetProtocol


async def ethernet_auto_detect():
    """
    Automatically detects and establishes an Ethernet connection to a device using Telnet.

    This asynchronous function creates a Telnet transport, initializes a device client,
    connects to the device, prints the connected device's IP address, and then closes the connection.
    """
    transport = TelnetProtocol()
    client = NV200Device(transport)
    await client.connect()
    print(f"Connected to device with IP: {transport.host}")
    await client.close()


if __name__ == "__main__":
    asyncio.run(ethernet_auto_detect())
