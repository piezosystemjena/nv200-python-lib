import asyncio

from nv200.shared_types import TransportType
from nv200.connection_utils import connect_to_single_device
from nv200.nv200_device import NV200Device


async def main():
    device = await connect_to_single_device(NV200Device, TransportType.SERIAL)

    slpf = device.setpoint_lpf
    await slpf.set_cutoff(200)  # Set cutoff frequency to 200 Hz
    await slpf.enable(False)    # Disable the setpoint low-pass filter
    print(f"Setpoint LPF Cutoff Frequency: {await slpf.get_cutoff()} Hz")


    plpf = device.position_lpf
    await plpf.set_cutoff(1000)  # Set cutoff frequency to 1000 Hz
    await plpf.enable(True)     # Enable the position low-pass filter
    print(f"Position LPF Cutoff Frequency: {await plpf.get_cutoff()} Hz")

    nf = device.notch_filter
    await nf.set_bandwidth(200)  # Set notch filter bandwidth to 200 Hz
    await nf.set_frequency(100)  # Set notch filter frequency to 100 Hz

    await device.close()

if __name__ == "__main__":
    asyncio.run(main())
