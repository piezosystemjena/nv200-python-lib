import asyncio
import math
import matplotlib.pyplot as plt
import aioserial
import serial
from matplotlib.ticker import AutoMinorLocator
import numpy as np
from nv200.device_interface import DeviceClient, PidLoopMode, StatusFlags
from nv200.transport_protocols import  TelnetProtocol, SerialProtocol
from nv200.data_recorder import DataRecorderSource, RecorderAutoStartMode, DataRecorder
from nv200.waveform_generator import WaveformGenerator




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


def prepare_plot_style():
    """
    Configures the plot style for a matplotlib figure with a dark background theme.
    """
    # use dark background
    plt.style.use('dark_background')

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

def show_plot():
    """
    Displays a plot with a legend.

    The legend is styled with a dark gray face color and edge color, 
    and it is displayed with a frame. The location of the legend is 
    set to the best position automatically, and the font size is set 
    to 10. The plot is shown in a blocking mode, ensuring the script 
    pauses until the plot window is closed.
    """
    plt.legend(facecolor='darkgray', edgecolor='darkgray', frameon=True, loc='best', fontsize=10)
    plt.show(block=True)



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
    rec_param = await recorder.set_recording_duration_ms(100)

    await recorder.start_recording()
    await device.move_to_position(80)
    await asyncio.sleep(0.4)
    print("Reading recorded data of both channels...")
    rec_data = await recorder.read_recorded_data()

    prepare_plot_style()
    # Compute time axis
    N = len(rec_data[0].data)
    t = np.arange(N) / rec_param.sample_freq * 1000 # Time values in ms
    plt.plot(t, rec_data[0].data, linestyle='-', color='orange', label=rec_data[0].source)
    plt.plot(t, rec_data[1].data, linestyle='-', color='green', label=rec_data[1].source)    
    show_plot()


async def run_tests(client: DeviceClient):
    """
    Asynchronously runs a series of tests on a DeviceClient instance.

    This function performs various operations such as reading and writing 
    to the client, setting and retrieving PID modes, and querying the 
    device's status and position. It is designed to test the functionality 
    of the DeviceClient and ensure proper communication with the server.
    """
    await basic_tests(client)
    await data_recorder_tests(client)




async def client_telnet_test():
    """
    Asynchronous function to test a Telnet connection to a device using the `TelnetTransport` 
    and `DeviceClient` classes.
    This function establishes a connection to a device, sends a series of commands, 
    reads responses, and then closes the connection.
    """
    print(await TelnetProtocol.discover_devices())
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
    #print(await SerialProtocol.discover_devices())
    transport = SerialProtocol(port="COM3")
    client = DeviceClient(transport)
    await client.connect()
    print(f"Connected to device on serial port: {transport.port}")
    await run_tests(client)
    await client.close()

async def waveform_generator_test():
    """
    Asynchronous function to test the functionality of the WaveformGenerator class.
    This function initializes a DeviceClient and a WaveformGenerator instance, 
    sets up the waveform generator, and starts it with specified parameters.
    """
    prepare_plot_style()
    transport = TelnetProtocol(MAC="00:80:A3:79:C6:18")  
    #transport = SerialProtocol(port="COM3")
    client = DeviceClient(transport)
    await client.connect()

    waveform_generator = WaveformGenerator(client)
    sine = waveform_generator.generate_sine_wave(freq_hz=0.1, low_level=0, high_level=80)
    plt.plot(sine.sample_times_ms, sine.values, linestyle='-', color='orange', label="Generated Sine Wave")
    print(f"Sample factor {sine.sample_factor}")
    print("Transferring waveform data to device...")
    #await waveform_generator.set_waveform(sine)


    recorder = DataRecorder(client)
    await recorder.set_data_source(0, DataRecorderSource.PIEZO_POSITION)
    await recorder.set_data_source(1, DataRecorderSource.PIEZO_VOLTAGE)
    await recorder.set_autostart_mode(RecorderAutoStartMode.START_ON_GRUN_COMMAND)
    #await recorder.set_recording_duration_ms(sine.cycle_time_ms * 1.2)
    await recorder.start_recording()

    print("Starting waveform generator...")
    await waveform_generator.start(cycles=1, start_index=0)
    await asyncio.sleep(sine.cycle_time_ms * 1.2 / 1000)

    print("Reading recorded data of both channels...")
    rec_data = await recorder.read_recorded_data()
    plt.plot(rec_data[0].sample_times_ms, rec_data[0].values, linestyle='-', color='purple', label=rec_data[0].source)
    plt.plot(rec_data[1].sample_times_ms, rec_data[1].values, linestyle='-', color='green', label=rec_data[1].source) 

    # Display the plot
    await client.close()
    show_plot()


async def test_serial_protocol():
    dev = aioserial.AioSerial(port="COM3", baudrate=115200, timeout=5)
    dev.xonxoff = False
    #await serial.write_async(b"gtarb,1\r\n")
    #await serial.write_async(b"cl,1\r\n")
    await dev.write_async(b"\r")
    data = await dev.read_until_async(serial.XON)
    print(f"Received: {data}")
    dev.close()




if __name__ == "__main__":
    #asyncio.run(client_telnet_test())
    #asyncio.run(client_serial_test())
    asyncio.run(waveform_generator_test())
    #asyncio.run(test_serial_protocol())

