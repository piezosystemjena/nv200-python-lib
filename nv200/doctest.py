import asyncio
from nv200.nv200_device import NV200Device
from nv200.shared_types import PidLoopMode
from nv200.connection_utils import connect_to_single_device


async def main_async():
    """
    Moves the device to a specified position using closed-loop control.
    """
    dev = await connect_to_single_device(NV200Device)
    print(f"Connected to device: {dev.device_info}")

    await dev.move_to_position(20)
    await asyncio.sleep(0.2)
    print(f"Current position: {await dev.get_current_position()}")

    # instead of using move_to_position, you can also use two separate commands
    # to set the PID mode and the setpoint
    await dev.set_pid_mode(PidLoopMode.CLOSED_LOOP)
    await dev.set_setpoint(0)
    await asyncio.sleep(0.2)
    print(f"Current position: {await dev.get_current_position()}")


if __name__ == "__main__":
    asyncio.run(main_async())