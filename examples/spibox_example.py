import asyncio
import matplotlib.pyplot as plt

import matplotlib_helpers
from nv200.connection_utils import connect_to_detected_device
from nv200.device_discovery import discover_devices
from nv200.shared_types import DiscoverFlags
from nv200.spibox_device import SpiBoxDevice
from nv200.waveform_generator import WaveformGenerator, WaveformType

async def spibox_test():
    """
    Asynchronous function to test the functionality of the SPI Box.
    """

    # Discover devices connected via USB interface
    print("Discovering devices connected via USB interface...")
    detected_devices = await discover_devices(
        DiscoverFlags.DETECT_SERIAL | DiscoverFlags.READ_DEVICE_INFO, 
        device_class=SpiBoxDevice
    )
    
    if not detected_devices:
        print("No devices found.")
        return
    
    # connect to the first detected device
    device : SpiBoxDevice = await connect_to_detected_device(detected_devices[0])
    print(f"Connected to device: {device.device_info}")
    
    # Move all channels to lowest and highest setpoints
    print("Moving all channels to lowest setpoints...")
    await device.set_setpoints_percent(0.0, 0.0, 0.0)
    await asyncio.sleep(1.0)

    print("Moving all channels to highest setpoints...")
    await device.set_setpoints_percent(100.0, 100.0, 100.0)
    await asyncio.sleep(1.0)

    positions = await device.get_setpoints_percent()
    print("Channel positions:", positions)


    # Create a waveform generator instance
    # Important: Pass None as device because the SpiBox is no NV200 device
    waveform_generator = WaveformGenerator(None)

    waveforms = []

    # Generate a sine waveforms for all channels
    for ch in range(3):
        waveform = waveform_generator.generate_waveform(
            waveform_type=WaveformType.SINE,
            freq_hz=20,
            low_level=0.0,
            high_level=100.0,
            phase_shift_rad= ch * (3.14159 / 2.0)  # Phase shift each channel by 90 degrees
        )

        waveforms.append(waveform)

    print("Transferring waveforms to device...")
    
    await device.set_waveform_cycles(3, 3, 3)
    await device.set_waveform_sample_factors(
        waveforms[0].sample_factor,
        waveforms[1].sample_factor,
        waveforms[2].sample_factor
    )
    await device.upload_waveform_samples(
        waveforms[0].values,
        waveforms[1].values,
        waveforms[2].values,
        lambda current, total: print(f"Upload progress: {current}/{total} samples")
    )

    # Start waveform output
    await device.start_waveforms()

    print("Waiting for waveform completion...")
    await device.await_waveform_completion()

    # Readback the waveform buffer (every 3rd sample, max 1000 samples)
    response = await device.get_waveform_response(
        3, 
        1000,
        lambda current, total: print(f"Readback progress: {current}/{total} samples")
    )

    # Use matplotlib to plot the recorded data
    matplotlib_helpers.prepare_plot_style()
    plt.plot(response[0].sample_times_ms, response[0].values, linestyle='-', color='orange', label='Channel 1')
    plt.plot(response[1].sample_times_ms, response[1].values, linestyle='-', color='green', label='Channel 2')   
    plt.plot(response[2].sample_times_ms, response[2].values, linestyle='-', color='blue', label='Channel 3')   
    matplotlib_helpers.show_plot()

    await device.close()


if __name__ == "__main__":
    print("Running SPI-Box test...")
    asyncio.run(spibox_test())