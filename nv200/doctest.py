import asyncio
from nv200.nv200_device import NV200Device
from nv200.shared_types import TransportType
from nv200.connection_utils import connect_to_single_device
from nv200.waveform_generator import WaveformGenerator

async def waveform_generator_test():
    # Create the device client using Telnet protocol
    device = await connect_to_single_device(device_class=NV200Device, transport_type=TransportType.SERIAL)

    # Initialize the waveform generator with the NV200 device
    waveform_generator = WaveformGenerator(device)

    # Generate a sine wave with a frequency of 1 Hz, low level of 0, and high level of 80 µm
    sine = waveform_generator.generate_sine_wave(freq_hz=1, low_level=0, high_level=80)
    print(f"Sample factor {sine.sample_factor}")

    # Transfer the waveform data to the device
    await waveform_generator.set_waveform(sine)

    # Start the waveform generator with 1 cycle and starting index of 0
    await waveform_generator.start(cycles=1, start_index=0)

    # Wait until the waveform generator finishes the move
    await waveform_generator.wait_until_finished()

    # Close the device client connection
    await device.close()

if __name__ == "__main__":
    asyncio.run(waveform_generator_test())