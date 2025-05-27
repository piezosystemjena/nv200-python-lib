import asyncio
from nv200.nv200_device import NV200Device 
from nv200.shared_types import DiscoverFlags
from nv200.device_discovery import discover_devices
from nv200.data_recorder import DataRecorder, DataRecorderSource, RecorderAutoStartMode
import maptplotlib_helpers
import matplotlib.pyplot as plt


async def data_recorder_test():
    """
    Asynchronous function to test the functionality of the DataRecorder with a given device.
    """
    print("Discovering devices...")
    detected_devices = await discover_devices(DiscoverFlags.DETECT_SERIAL)
    if not detected_devices:
        print("No devices found.")
        return

    device = NV200Device.from_detected_device(detected_devices[0])
    await device.connect()

    # Move the device to its initial position and wait for a short duration to stabilize
    await device.move_to_position(0)
    await asyncio.sleep(0.4)

    # Create a DataRecorder instance and configure it
    recorder = DataRecorder(device)
    await recorder.set_data_source(0, DataRecorderSource.PIEZO_POSITION)
    await recorder.set_data_source(1, DataRecorderSource.PIEZO_VOLTAGE)
    await recorder.set_autostart_mode(RecorderAutoStartMode.START_ON_SET_COMMAND)
    rec_param = await recorder.set_recording_duration_ms(100)
    print("Recording parameters:")
    print(f"  Used buffer entries: {rec_param.bufsize}")
    print(f"  Stride: {rec_param.stride}")
    print(f"  Sample frequency (Hz): {rec_param.sample_freq}")

    # Start recording and move the device to a new position to record the parameters
    await recorder.start_recording()
    await device.move_to_position(80)
    await asyncio.sleep(0.4)
    print("Reading recorded data of both channels...")

    # Read the recorded data from the DataRecorder
    rec_data = await recorder.read_recorded_data()

    # Use matplotlib to plot the recorded data
    maptplotlib_helpers.prepare_plot_style()
    plt.plot(rec_data[0].sample_times_ms, rec_data[0].values, linestyle='-', color='orange', label=rec_data[0].source)
    plt.plot(rec_data[1].sample_times_ms, rec_data[1].values, linestyle='-', color='green', label=rec_data[1].source)   
    maptplotlib_helpers.show_plot()

    device.close()


if __name__ == "__main__":
    print("Running data recorder test...")
    asyncio.run(data_recorder_test())