import asyncio
from nv200.device_discovery import discover_devices
from nv200.device_factory import create_device_from_detected_device
from nv200.shared_types import DiscoverFlags

async def main():
    devices = await discover_devices(DiscoverFlags.ALL_INTERFACES | DiscoverFlags.READ_DEVICE_INFO)
    device = create_device_from_detected_device(devices[0])
    await device.connect()

    # Perform your device operations here

    await device.close()

if __name__ == "__main__":
    asyncio.run(main())
