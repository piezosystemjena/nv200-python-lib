import asyncio
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import numpy as np
from nv200_driver import DeviceClient, PidLoopMode, StatusFlags, TelnetProtocol, SerialProtocol
from data_recorder import DataRecorderSource, RecorderAutoStartMode, DataRecorder




async def basic_tests(client: DeviceClient):
    """
    Performs a series of basic tests on the provided DeviceClient instance.
    """
    response = await client.read('')
    print(f"Server response: {response}")    
    await client.write('modsrc,0')
    await client.write('cl,1')
    await client.write('set,40')
    await asyncio.sleep(0.1)
    response = await client.read('meas')
    print(f"Server response: {response}")
    response = await client.read('cl')
    print(f"Server response: {response}")
    print("Current position:", await client.get_current_position())
    await client.set_pid_mode(PidLoopMode.CLOSED_LOOP)
    await client.set_pid_mode(PidLoopMode.OPEN_LOOP)
    value = await client.get_pid_mode()
    print("PID mode:", value)
    await client.set_setpoint(0)
    setpoint = await client.get_setpoint()
    print("Setpoint:", setpoint)
    print("Current position:", await client.get_current_position())
    print("Heat sink temperature:", await client.get_heat_sink_temperature())
    print(await client.get_status_register())
    print("Is status flag ACTUATOR_CONNECTED set: ", await client.is_status_flag_set(StatusFlags.ACTUATOR_CONNECTED))
    print("posmin:", await client.read_float_value('posmin'))
    print("posmax:", await client.read_float_value('posmax'))
    print("avmin:", await client.read_float_value('avmin'))
    print("avmax:", await client.read_float_value('avmax'))


def plot_recorded_data(rec_data: list[DataRecorder.ChannelRecordingData], sample_rate: float):
    """
    Plots recorded data from an NV200 Data Recorder.
    This function takes a list of channel recording data and a sample rate, 
    computes the time axis, and plots the data using a dark background style.

    Args:
        rec_data (list[DataRecorder.ChannelRecordingData]): 
            A list containing channel recording data objects. Each object 
            should have a `data` attribute (list of recorded values) and a 
            `source` attribute (label for the data source).
        sample_rate (float): 
            The sampling rate of the recorded data in Hz.

    Behavior:
        - Computes the time axis in milliseconds based on the sample rate.
        - Plots the data for the first two channels in the list with distinct 
          colors and labels.
        - Applies a dark background style with customized grid, ticks, and 
          spines for better visualization.
        - Displays the plot with appropriate labels, title, and legend.
        
    Note:
        Ensure that `rec_data` contains at least two channels of data for 
        proper plotting.
    """
    # Compute time axis
    N = len(rec_data[0].data)
    t = np.arange(N) / sample_rate * 1000 # Time values in ms
    
    # use dark background
    plt.style.use('dark_background')

    # Plot the data
    plt.plot(t, rec_data[0].data, linestyle='-', color='orange', label=rec_data[0].source)
    plt.plot(t, rec_data[1].data, linestyle='-', color='green', label=rec_data[1].source)

    # Labels and title
    plt.xlabel("Time (ms)")
    plt.ylabel("Value")
    plt.title("Sampled Data from NV200 Data Recorder")

    # Show grid and legend
    plt.grid(True, color='darkgray', linestyle='--', linewidth=0.5)
    plt.minorticks_on()
    plt.grid(which='minor', color='darkgray', linestyle=':', linewidth=0.5)
    plt.legend(facecolor='darkgray', edgecolor='darkgray', frameon=True, loc='best', fontsize=10)

    ax = plt.gca()
    ax.spines['top'].set_color('darkgray')
    ax.spines['right'].set_color('darkgray')
    ax.spines['bottom'].set_color('darkgray')
    ax.spines['left'].set_color('darkgray')

    # Set tick parameters for dark grey color
    ax.tick_params(axis='x', colors='darkgray')
    ax.tick_params(axis='y', colors='darkgray')

    # Display the plot
    plt.show()


async def data_recorder_tests(device: DeviceClient):
    """
    Asynchronous function to test the functionality of the DataRecorder with a given device.
    """
    await device.move_to_position(0)
    await asyncio.sleep(0.4)

    recorder = DataRecorder(device)
    await recorder.set_data_source(0, DataRecorderSource.PIEZO_POSITION)
    await recorder.set_data_source(1, DataRecorderSource.PIEZO_VOLTAGE)
    await recorder.set_autostart_mode(RecorderAutoStartMode.START_ON_SET_COMMAND)
    rec_param = await recorder.set_recording_duration_ms(307)

    await recorder.start_recording()
    await device.move_to_position(80)
    await asyncio.sleep(0.4)
    print("Reading recorded data of both channels...")
    rec_data = await recorder.read_recorded_data()
    plot_recorded_data(rec_data, rec_param.sample_freq)


async def run_tests(client: DeviceClient):
    """
    Asynchronously runs a series of tests on a DeviceClient instance.

    This function performs various operations such as reading and writing 
    to the client, setting and retrieving PID modes, and querying the 
    device's status and position. It is designed to test the functionality 
    of the DeviceClient and ensure proper communication with the server.
    """
    #await basic_tests(client)
    await data_recorder_tests(client)




async def client_telnet_test():
    """
    Asynchronous function to test a Telnet connection to a device using the `TelnetTransport` 
    and `DeviceClient` classes.
    This function establishes a connection to a device, sends a series of commands, 
    reads responses, and then closes the connection.
    """
    transport = TelnetProtocol(MAC="00:80:A3:79:C6:18")
    #transport = TelnetTransport()
    client = DeviceClient(transport)
    await client.connect()
    print(f"Connected to device with IP: {transport.host}")
    await run_tests(client)
    await client.close()



async def client_serial_test():
    """
    Asynchronous function to test serial communication with a device client.
    This function establishes a connection to a device using a serial transport,
    sends a series of commands, and retrieves responses from the device.
    """
    transport = SerialProtocol()
    client = DeviceClient(transport)
    await client.connect()
    print(f"Connected to device on serial port: {transport.port}")
    await run_tests(client)
    await client.close()


if __name__ == "__main__":
    asyncio.run(client_telnet_test())
    #asyncio.run(client_serial_test())
