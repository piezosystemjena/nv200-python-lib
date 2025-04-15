import asyncio
from nv200.device_interface import DeviceClient
from nv200.transport_protocols import SerialProtocol


async def serial_port_auto_detect():
    transport = SerialProtocol()
    client = DeviceClient(transport)
    await client.connect()
    print(f"Connected to device on serial port: {transport.port}")
    await client.close()


if __name__ == "__main__":
    asyncio.run(serial_port_auto_detect())
