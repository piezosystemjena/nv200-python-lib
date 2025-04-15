import asyncio
from nv200.device_interface import DeviceClient
from nv200.transport_protocols import TelnetProtocol


async def ethernet_auto_detect():
    transport = TelnetProtocol()
    client = DeviceClient(transport)
    await client.connect()
    print(f"Connected to device with IP: {transport.host}")
    await client.close()


if __name__ == "__main__":
    asyncio.run(ethernet_auto_detect())
