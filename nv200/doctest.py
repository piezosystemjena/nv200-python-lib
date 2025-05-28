import asyncio
from nv200.shared_types import DetectedDevice
from nv200.device_discovery import discover_devices
from nv200.nv200_device import NV200Device

async def main_async():
    print("Discovering devices...")
    detected_devices = await discover_devices()
    
    if not detected_devices:
        print("No devices found.")
        return

    # Create a device client for the first detected device
    device = NV200Device.from_detected_device(detected_devices[0])
    await device.connect()

# Running the async main function
if __name__ == "__main__":
    asyncio.run(main_async())
