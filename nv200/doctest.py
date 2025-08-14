import asyncio
from nv200.nv200_device import NV200Device
from nv200.waveform_generator import WaveformGenerator, WaveformType, WaveformUnit
from nv200.connection_utils import connect_to_single_device

async def waveform_generator_test():
    # Connect to first device
    device = await connect_to_single_device(NV200Device)

    # Initialize the waveform generator with the NV200 device
    waveform_generator = WaveformGenerator(device)

    # Generate a sine wave with a frequency of 1 Hz, low level of 0, and high level of 80 µm
    sine = waveform_generator.generate_waveform(WaveformType.SINE, freq_hz=1, low_level=0, high_level=80)
    print(f"Sample factor {sine.sample_factor}")

    # Transfer the waveform data to the device - the waveform is given in position units
    await waveform_generator.set_waveform(sine, WaveformUnit.POSITION)

    # Start the waveform generator with 1 cycle and starting index of 0
    await waveform_generator.start(cycles=1, start_index=0)

    # Wait until the waveform generator finishes the move
    await waveform_generator.wait_until_finished()

    # Close the device client connection
    await device.close()

if __name__ == "__main__":
    asyncio.run(waveform_generator_test())
