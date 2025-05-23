import asyncio
from nv200.device_discovery import discover_devices, DiscoverFlags


# async Main execution
async def main_async():
    """
    Asynchronously discovers available devices and prints their information.
    """
    print("\nDiscovering devices...")
    devices = await discover_devices()
    
    if not devices:
        print("No devices found.")
    else:
        print(f"Found {len(devices)} device(s):")
        for device in devices:
            print(device)

    print("\nDiscovering devices with extended information...")
    devices = await discover_devices(DiscoverFlags.ALL_INTERFACES | DiscoverFlags.EXTENDED_INFO)	
    
    if not devices:
        print("No devices found.")
    else:
        print(f"Found {len(devices)} device(s):")
        for device in devices:
            print(device)


# Running the async main function
if __name__ == "__main__":
    asyncio.run(main_async())

