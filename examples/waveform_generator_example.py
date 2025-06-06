import asyncio
from nv200.nv200_device import NV200Device
from nv200.waveform_generator import WaveformGenerator
from nv200.shared_types import TransportType
from nv200.connection_utils import connect_to_single_device
from nv200.data_recorder import DataRecorder, DataRecorderSource, RecorderAutoStartMode
import maptplotlib_helpers
import matplotlib.pyplot as plt



async def waveform_generator_test():
    """
    Asynchronous function to test the functionality of the WaveformGenerator class.
    """

    # Connect to the one and only NV200 device connected via serial port
    client = await connect_to_single_device(NV200Device, TransportType.SERIAL)   

    # Generate a sine waveform with specified frequency and amplitude and
    # transfer it to the device
    print("Generating sine waveform...")
    waveform_generator = WaveformGenerator(client)
    sine = waveform_generator.generate_sine_wave(freq_hz=10, low_level=0, high_level=80)
    print(f"Sample factor {sine.sample_factor}")
    print("Transferring waveform data to device...")
    await waveform_generator.set_waveform(sine)

    # Create a DataRecorder instance and configure it to record the movement of the piezo actuator
    recorder = DataRecorder(client)
    await recorder.set_data_source(0, DataRecorderSource.PIEZO_POSITION)
    await recorder.set_data_source(1, DataRecorderSource.PIEZO_VOLTAGE)
    await recorder.set_autostart_mode(RecorderAutoStartMode.START_ON_WAVEFORM_GEN_RUN)
    await recorder.set_recording_duration_ms(sine.cycle_time_ms * 1.2)
    await recorder.start_recording()

    # Start the waveform generator to run the sine wave for one cycle. This will also 
    # trigger the DataRecorder to start recording
    print("Starting waveform generator...")
    await waveform_generator.start(cycles=1, start_index=0)
    print(f"Is running: {await waveform_generator.is_running()}")
    await recorder.wait_until_finished()
    print(f"Is running: {await waveform_generator.is_running()}")

    # Read the recorded data from the DataRecorder
    print("Reading recorded data of both channels...")
    rec_data = await recorder.read_recorded_data()

    # Use matplotlib to plot the generated sine wave and the recorded data
    maptplotlib_helpers.prepare_plot_style()
    plt.plot(sine.sample_times_ms, sine.values, linestyle='-', color='orange', label="Generated Sine Wave")
    plt.plot(rec_data[0].sample_times_ms, rec_data[0].values, linestyle='-', color='purple', label=rec_data[0].source)
    plt.plot(rec_data[1].sample_times_ms, rec_data[1].values, linestyle='-', color='green', label=rec_data[1].source) 
    maptplotlib_helpers.show_plot()

    await client.close()


if __name__ == "__main__":
    asyncio.run(waveform_generator_test())
