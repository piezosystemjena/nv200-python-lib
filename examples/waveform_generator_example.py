import asyncio
from nv200.nv200_device import NV200Device
from nv200.transport_protocol import TelnetProtocol
from nv200.waveform_generator import WaveformGenerator
from nv200.shared_types import TransportType
from nv200.connection_utils import connect_to_single_device

async def waveform_generator_test():
    """
    Asynchronous function to test the functionality of the WaveformGenerator class.
    This function initializes a DeviceClient and a WaveformGenerator instance, 
    sets up the waveform generator, and starts it with specified parameters.
    """
    # Create the device client using Telnet protocol
    device = await connect_to_single_device(TransportType.SERIAL)

    # Initialize the waveform generator with the device client and
    # generate a sine wave that moves the piezo in a sine wave of 1 Hz from 0 to 80 µm
    waveform_generator = WaveformGenerator(device)
    sine = waveform_generator.generate_sine_wave(freq_hz=1, low_level=0, high_level=80)
    print(f"Sample factor {sine.sample_factor}")
    print("Transferring waveform data to device...")

    # Transfer the waveform data to the device
    await waveform_generator.set_waveform(sine)

    # Start the waveform generator with 1 cycle and starting index of 0
    # and wait until it finishes the move
    print("Starting waveform generator...")
    await waveform_generator.start(cycles=1, start_index=0)
    await waveform_generator.wait_until_finished()

    # Close the device client connection
    await device.close()

if __name__ == "__main__":
    asyncio.run(waveform_generator_test())
