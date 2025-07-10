import asyncio
from nv200.nv200_device import NV200Device
from nv200.shared_types import TransportType
from nv200.connection_utils import connect_to_single_device


async def ethernet_auto_detect():
    """
    Automatically detects and establishes an Ethernet connection to the first detected device using Telnet.
    """
    device = await connect_to_single_device(NV200Device, TransportType.TELNET)
    print(f"Connected to device: {device.device_info}")
    await  device.close()


if __name__ == "__main__":
    asyncio.run(ethernet_auto_detect())
