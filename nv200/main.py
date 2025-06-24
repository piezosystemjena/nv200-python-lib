import asyncio
import numpy as np
import matplotlib.pyplot as plt
import aioserial
import serial
import time
import configparser
from typing import cast, Tuple, List, Dict
from nv200.telnet_protocol import TelnetProtocol
from nv200.serial_protocol import SerialProtocol
from nv200.transport_protocol import TransportProtocol
from nv200.data_recorder import DataRecorderSource, RecorderAutoStartMode, DataRecorder
from nv200.waveform_generator import WaveformGenerator
from nv200.shared_types import DiscoverFlags, PidLoopMode, StatusFlags, TransportType
from nv200.device_discovery import discover_devices
from nv200.nv200_device import NV200Device
from nv200.spibox_device import SpiBoxDevice
from rich.traceback import install as install_rich_traceback
from rich.logging import RichHandler

import nv200.connection_utils
import logging


# Global module locker
logger = logging.getLogger(__name__)


async def basic_tests(client: NV200Device):
    """
    Performs a series of basic tests on the provided DeviceClient instance.
    """
    response = await client.read_response_string('')
    print(f"Server response: {response}")    
    await client.write('modsrc,0')
    await client.write('cl,1')
    await client.write('set,40')
    await asyncio.sleep(0.1)
    response = await client.read_response_string('meas')
    print(f"Server response: {response}")
    response = await client.read_response_string('cl')
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



async def data_recorder_tests(device: NV200Device):
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


async def run_tests(client: NV200Device):
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
    #print(await TelnetProtocol.discover_devices(DiscoverFlags.DETECT_ETHERNET))
    #transport = TelnetProtocol(host="192.168.101.5")
    transport = TelnetProtocol(MAC="00:80:A3:79:C6:18")  # Replace with your device's MAC address
    client = NV200Device(transport)
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
    client = NV200Device(transport)
    await client.connect()
    print(f"Connected to device on serial port: {transport.port}")
    await run_tests(client)
    await client.close()


async def waveform_generator_test():
    """
    Asynchronous function to test the functionality of the WaveformGenerator class.
    """
    async def print_progress(current_index: int, total: int):
        percent = 100 * current_index / total
        print(f"[{percent:.1f}%] Set value {current_index} of {total}")

    prepare_plot_style()
    device = await nv200.connection_utils.connect_to_single_device(
        device_class=NV200Device, 
        transport_type=TransportType.SERIAL)  

    #await client.write('setlpf,200')
    #await client.write('setlpon,0')
    #await client.write('poslpf,1000')
    #await client.write('poslpon,1')

    await device.set_pid_mode(PidLoopMode.CLOSED_LOOP)
    pos_range = await device.get_position_range()
    waveform_generator = WaveformGenerator(device)
    waveform_generator.generate_time_samples_list(freq_hz=1)

    sine = waveform_generator.generate_sine_wave(freq_hz=10, low_level=pos_range[0], high_level=pos_range[1])
    print(sine.cycle_time_ms)
    plt.plot(sine.sample_times_ms, sine.values, linestyle='-', color='orange', label="Generated Sine Wave")
    print(f"Sample factor {sine.sample_factor}")
    print("Transferring waveform data to device...")
    await waveform_generator.set_waveform(sine, on_progress=print_progress)


    recorder = DataRecorder(device)
    await recorder.set_data_source(0, DataRecorderSource.PIEZO_POSITION)
    await recorder.set_data_source(1, DataRecorderSource.PIEZO_VOLTAGE)
    await recorder.set_autostart_mode(RecorderAutoStartMode.START_ON_WAVEFORM_GEN_RUN)
    await recorder.set_recording_duration_ms(sine.cycle_time_ms * 1.2)
    await recorder.start_recording()

    print("Starting waveform generator...")
    await waveform_generator.start(cycles=20, start_index=0)
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
    await device.close()
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

    t=np.arange(0, Cycles * TimePeriod , dt)
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
    devices = await discover_devices(DiscoverFlags.ALL_INTERFACES | DiscoverFlags.READ_DEVICE_INFO)
    
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
    client = NV200Device(transport)
    await client.connect()
    print(f"Connected to device on serial port: {transport.port}")
    print("Actor: ", await client.get_actuator_name())
    print("Serial: ", await client.get_actuator_serial_number())
    print("Actuator type: ", await client.get_actuator_description())
    await client.close()


def setup_logging():
    """
    Configures the logging settings for the application.
    """
    # logging.basicConfig(
    #     level=logging.DEBUG,
    #     format='%(asctime)s.%(msecs)03d | %(levelname)-6s | %(name)-25s | %(message)s',
    #     datefmt='%H:%M:%S'
    # )

    # rich logging and exception handling
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s.%(msecs)03d | %(name)-25s | %(message)s',
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, )]
    )
    install_rich_traceback(show_locals=True)

    # List all loggers
    #for name in logging.root.manager.loggerDict:
    #    print(name)

    #logging.getLogger("nv200.device_discovery").setLevel(logging.DEBUG)
    logging.getLogger("nv200.telnet_protocol").setLevel(logging.DEBUG)



async def read_write_tests():
    """
    Test some generic low-level read/write methods
    """
    transport = SerialProtocol(port="COM3")
    device_client = NV200Device(transport)
    await device_client.connect()
    print(f"Connected to device on serial port: {transport.port}")
    await device_client.write('cl,0')
    response = await device_client.read_response_string('cl')
    print(response)
    response = await device_client.read_response('set')
    print(response)
    response = await device_client.read_values('recout,0,0,1')
    print(response)
    response = await device_client.read_float_value('set')
    print(response)
    response = await device_client.read_int_value('cl')
    print(response)
    response = await device_client.read_string_value('desc')
    print(response)
    await device_client.close()


async def test_quick_connect():
    """
    Test the quick connect functionality to connect to a device.
    """
    device = await nv200.connection_utils.connect_to_single_device()
    print(f"Actuator name: {await device.get_actuator_name()}")
    await device.close()


async def test_serial_protocol_auto_detect():
    """
    Test the automatic detection of serial ports for NV200 devices.
    """
    transport = SerialProtocol()
    client = NV200Device(transport)
    await client.connect()
    print(f"Connected to device on serial port: {transport.port}")
    await client.close()

def generate_sine_wave(
    freq: float,
    low: float = 0.0,
    high: float = 100.0,
    phase_deg: float = 0.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates one full cycle of a sine wave as a NumPy array with specified frequency,
    amplitude range, and phase. The number of samples is calculated to achieve
    one full cycle at a fixed sample rate.

    Args:
        freq (float): Frequency of the sine wave in Hertz. Must be > 0.
        low (float, optional): Minimum value of the output wave. Defaults to 0.0.
        high (float, optional): Maximum value of the output wave. Defaults to 1.0.
        phase_deg (float, optional): Phase offset in degrees. Defaults to 0.0.

    Returns:
        Tuple[np.ndarray, np.ndarray]: A tuple containing:
            - The time array (np.ndarray) for one cycle.
            - The generated sine wave samples for one cycle, scaled to the [low, high] range (np.ndarray).
    Raises:
        ValueError: If freq is not positive.
    """
    if freq <= 0:
        raise ValueError("Frequency (freq) must be a positive value.")

    # Fixed sample rate as per device specification
    sample_rate: int = 20000 # Hz

    # Calculate the number of samples required for exactly one full cycle
    # samples_per_cycle = sample_rate / freq
    # We need to ensure we get an integer number of samples.
    # If samples_per_cycle is not an integer, np.linspace will handle it,
    # but for clarity regarding discrete samples, it's often floored or ceiled.
    # For a *full* cycle, we need enough samples.
    
    # Calculate the period of the wave (time for one cycle)
    period = 1.0 / freq # seconds

    # Calculate the number of samples needed for one period at the given sample_rate
    # We take ceil to ensure we get at least one full cycle if freq is very low or
    # if sample_rate is not an exact multiple of freq.
    samples_required = int(np.ceil(period * sample_rate))
    
    # Ensure a minimum of 2 samples to define a wave (e.g., for very high frequencies)
    if samples_required < 2:
        samples_required = 2
    
    # The `linspace` function defines the time points for the generated samples.
    # It will span exactly one period (from 0 up to, but not including, the end of the period)
    # The endpoint=False ensures we don't duplicate the start point if samples_required
    # happens to be exactly sample_rate / freq.
    t = np.linspace(0, period, samples_required, endpoint=False)
    
    phase_rad = np.deg2rad(phase_deg)  # Convert phase to radians
    wave = np.sin(2 * np.pi * freq * t + phase_rad)
    
    # Scale from [-1, 1] to [low, high]
    scaled_wave = low + (wave + 1) * (high - low) / 2
    
    print(f"Generated wave for {freq} Hz: {samples_required} samples (duration: {period:.4f}s)")
    
    return t, scaled_wave



async def spi_box_test():
    prepare_plot_style()
    transport = SerialProtocol(port="COM5")
    dev = SpiBoxDevice(transport)
    await dev.connect(auto_adjust_comm_params=False)

    #dev = await nv200.connection_utils.connect_to_single_device(SpiBoxDevice, TransportType.SERIAL)
    await asyncio.sleep(0.1)
    #print(await dev.get_device_type())
    await asyncio.sleep(0.1)

    ch1 = generate_sine_wave(freq=20, low=0.0, high=100.0)
    ch2 = generate_sine_wave(freq=20, low=0.0, high=100.0)
    ch3 = generate_sine_wave(freq=20, low=0.0, high=100.0)
    plt.plot(ch1[0], ch3[1], linestyle='-', color='green', label="Channel 1 TX")
    print(len(ch1[1]))
    values : List[np.ndarray] 
    values = await dev.set_waveforms(ch1[1], ch2[1], ch3[1])
    print(values)
    plt.plot(ch1[0], values[2], linestyle='-', color='orange', label="Channel RX")
    show_plot()

    # print(await dev.set_setpoints_percent(0, 0, 0))
    # await asyncio.sleep(1)
    # print(await dev.set_setpoints_percent(100, 100, 100))
    # await asyncio.sleep(1)
    
    transport = cast(SerialProtocol, dev.transport_protocol)
    # await transport.write('usbdata,0000,0000,0000\r\n')
    # s = transport.serial
    # await asyncio.sleep(0.1)
    # print(s.read_all())
    # await asyncio.sleep(0.1)
    # respone = await dev.read_response_string('usbdata,0000,0000,0000\r\n')
    # print(f"Response 1: {respone}")
    # await asyncio.sleep(0.1)
    # respone = await dev.read_response_string('usbdata,0001,0002,0003\r\n')
    # print(f"Response 2: {respone}")
    # await asyncio.sleep(0.1)
    # respone = await dev.read_response_string('usbdata,0000,0000,0000')
    # print(f"Response: {respone}")
    # await asyncio.sleep(0.1)

    # transport = cast(SerialProtocol, dev.transport_protocol)
    # await transport.write('totalsamplex,200\r\n')
    # await transport.write('totalsampley,200\r\n')
    # await transport.write('totalsamplez,200\r\n')

    # print("Writing multiple values...")
    # await transport.write('usbdata,')
    # for i in range(100):
    #     await transport.write('0000,0000,0000\r')
    # for i in range(100):
    #     await transport.write('fffe,fffe,fffe\r')
    # await transport.write('\n')
    
    # print("Done writing values - reading response...")
    # print(await transport.read_message(10))
    #print(await transport.read_until(TransportProtocol.LF, timeout=10))

    # s = transport.serial
    # for i in range(10):
    #     await asyncio.sleep(0.1)
    #     print(s.read_all())

    # await transport.write('0001,0002,0003\r')
    # await asyncio.sleep(0.2)
    # print(s.read_all())  
    # await transport.write('0010,0020,0030\r\n')
    # await asyncio.sleep(0.1)
    # print(s.read_all())  
    # await asyncio.sleep(0.1)
    # print(s.read_all())  
        
    
    #respone = await dev.read_response_string('usbdata,0000,0000,0000\r0001,0002,0003\r0010,0020,0030\r\n', 2)
    #print(f"Response: {respone}")
    
    #print(await s.read_until_async(b'\n'))

    #response = await dev.write('usbdata,0000,0000,0000')
    #print(repr(response))
    await dev.close()

async def export_actuator_config(filename: str = ""):
    """
    Exports the configuration of the connected actuator to a file.
    """
    device = await nv200.connection_utils.connect_to_single_device(NV200Device, TransportType.TELNET, "192.168.101.2")
    filepath = await device.export_actuator_config()
    #await device.import_actuator_config(filepath)
    await device.close()



if __name__ == "__main__":
    setup_logging()

    #asyncio.run(client_telnet_test())
    #asyncio.run(client_serial_test())
    asyncio.run(waveform_generator_test())
    #asyncio.run(test_serial_protocol())
    #test_numpy_waveform()
    #asyncio.run(configure_xport())
    #asyncio.run(test_discover_devices())
    #asyncio.run(test_discover_devices())
    #asyncio.run(test_device_type())
    #asyncio.run(read_write_tests())
    #asyncio.run(test_quick_connect())
    #asyncio.run(test_serial_protocol_auto_detect())
    #asyncio.run(spi_box_test())
    #asyncio.run(export_actuator_config())
