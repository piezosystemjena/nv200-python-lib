import sys
import asyncio
from typing import List, Dict
from nv200.device_types import DetectedDevice
from nv200.device_discovery import discover_devices



# async Main execution
async def main_async():
    """
    Asynchronously discovers available devices and prints their information.
    """
    print("Discovering devices...")
    devices = await discover_devices()
    
    if not devices:
        print("No devices found.")
    else:
        print(f"Found {len(devices)} device(s):")
        for device in devices:
            print(device)


# Running the async main function
if __name__ == "__main__":
    asyncio.run(main_async())
    #main()
    #asyncio.run(configure_flow_control("192.168.10.177", FlowControlMode.XON_XOFF))
