import asyncio
from nv200.connection_utils import connect_to_single_device
from nv200.nv200_device import NV200Device
from nv200.device_base import PiezoDeviceBase

async def main_async():
    device = await connect_to_single_device(NV200Device)
    PiezoDeviceBase.CMD_CACHE_ENABLED = False  # disable globally
    pidmode = await device.get_pid_mode() # always reads from device
    print(pidmode)

    PiezoDeviceBase.CMD_CACHE_ENABLED = True  # enable globally
    pidmode = await device.get_pid_mode()  # uses cache if available
    print(pidmode)

# Running the async main function
if __name__ == "__main__":
    asyncio.run(main_async())
