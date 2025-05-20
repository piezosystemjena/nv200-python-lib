import asyncio
import math
import time
import numpy as np
import matplotlib.pyplot as plt
import telnetlib3
import aioserial
import serial
from matplotlib.ticker import AutoMinorLocator
import numpy as np
from nv200.device_interface import DeviceClient, PidLoopMode, StatusFlags
from nv200.transport_protocols import  TelnetProtocol, SerialProtocol
from nv200.data_recorder import DataRecorderSource, RecorderAutoStartMode, DataRecorder
from nv200.waveform_generator import WaveformGenerator
from nv200.utils import wait_until
from nv200.device_types import DetectedDevice
from nv200.device_discovery import discover_devices
import logging
from functools import wraps


# Global module locker
logger = logging.getLogger(__name__)


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
    prepare_plot_style()
    plt.plot(rec_data[0].sample_times_ms, rec_data[0].values, linestyle='-', color='orange', label=rec_data[0].source)
    plt.plot(rec_data[1].sample_times_ms, rec_data[1].values, linestyle='-', color='green', label=rec_data[1].source)   
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
    #await data_recorder_tests(client)




async def client_telnet_test():
    """
    Asynchronous function to test a Telnet connection to a device using the `TelnetTransport` 
    and `DeviceClient` classes.
    This function establishes a connection to a device, sends a series of commands, 
    reads responses, and then closes the connection.
    """
    print(await TelnetProtocol.discover_devices())
    #transport = TelnetProtocol(MAC="00:80:A3:79:C6:18")  
    transport = TelnetProtocol(host="192.168.10.103")  
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

    await client.write('setlpf,200')
    await client.write('setlpon,0')
    await client.write('poslpf,1000')
    await client.write('poslpon,1')
    waveform_generator = WaveformGenerator(client)
    sine = waveform_generator.generate_sine_wave(freq_hz=0.25, low_level=0, high_level=80)
    plt.plot(sine.sample_times_ms, sine.values, linestyle='-', color='orange', label="Generated Sine Wave")
    print(f"Sample factor {sine.sample_factor}")
    print("Transferring waveform data to device...")
    #await waveform_generator.set_waveform(sine)


    recorder = DataRecorder(client)
    await recorder.set_data_source(0, DataRecorderSource.PIEZO_POSITION)
    await recorder.set_data_source(1, DataRecorderSource.PIEZO_VOLTAGE)
    await recorder.set_autostart_mode(RecorderAutoStartMode.START_ON_WAVEFORM_GEN_RUN)
    await recorder.set_recording_duration_ms(sine.cycle_time_ms * 1.2)
    await recorder.start_recording()

    print("Starting waveform generator...")
    await waveform_generator.start(cycles=1, start_index=0)
    print(f"Is running: {await waveform_generator.is_running()}")
    #await waveform_generator.wait_until_finished()
    await recorder.wait_until_finished()
    print(f"Is running: {await waveform_generator.is_running()}")

    print("Reading recorded data of both channels...")
    rec_data = await recorder.read_recorded_data()
    plt.plot(rec_data[0].sample_times_ms, rec_data[0].values, linestyle='-', color='purple', label=rec_data[0].source)
    plt.plot(rec_data[1].sample_times_ms, rec_data[1].values, linestyle='-', color='green', label=rec_data[1].source) 
    print(f"rec_data[1].source: {rec_data[1].source}")

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

def test_numpy_waveform():
    percent=30.0
    TimePeriod=1.0
    Cycles=10
    dt=0.01 

    t=np.arange(0, Cycles * TimePeriod , dt); 
    pwm= t%TimePeriod<TimePeriod*percent/100 


    # Plot the rectangular wave (square wave with controlled duty cycle)
    plt.subplot(2, 1, 2)
    plt.plot(t, pwm)

    plt.tight_layout()
    plt.show()


async def test_discover_devices():
    """
    Asynchronously discovers available devices and prints their information.
    """
    logging.getLogger("nv200.device_discovery").setLevel(logging.DEBUG)
    logging.getLogger("nv200.transport_protocols").setLevel(logging.DEBUG)   
    
    print("Discovering devices...")
    devices = await discover_devices(full_info=True)
    
    if not devices:
        print("No devices found.")
    else:
        print(f"Found {len(devices)} device(s):")
        for device in devices:
            print(device)


async def test_device_client_interface():
    """
    Asynchronously tests the DeviceClient interface by connecting to a device and performing basic operations.
    """
    transport = SerialProtocol(port="COM3")
    client = DeviceClient(transport)
    await client.connect()
    print(f"Connected to device on serial port: {transport.port}")
    print("Actor: ", await client.get_actuator_name())
    print("Serial: ", await client.get_acctuator_serial_number())
    print("Actuator type: ", await client.get_actuator_description())
    await client.close()


async def test_device_type():
    logger.setLevel(logging.DEBUG)

    transport = TelnetProtocol(host="192.168.10.152")
    client = DeviceClient(transport)
    await client.connect()
    #print("Actor: ", await client.get_actuator_name())
    #print("Serial: ", await client.get_acctuator_serial_number())
    #print("Actuator type: ", await client.get_actuator_description())
    logger.debug("Reading param...")
    logger.debug(await client.get_device_type())
    await client.close()


def setup_logging():
    """
    Configures the logging settings for the application.
    """
    logging.basicConfig(
        level=logging.WARN,
        format='%(asctime)s.%(msecs)03d | %(levelname)-6s | %(name)-25s | %(message)s',
        datefmt='%H:%M:%S'
    )


if __name__ == "__main__":
    setup_logging()
    #asyncio.run(test_discover_devices())
    #asyncio.run(client_telnet_test())
    #asyncio.run(client_serial_test())
    #asyncio.run(waveform_generator_test())
    #asyncio.run(test_serial_protocol())
    #test_numpy_waveform()
    #asyncio.run(configure_xport())
    #asyncio.run(test_discover_devices())
    asyncio.run(test_device_type())

