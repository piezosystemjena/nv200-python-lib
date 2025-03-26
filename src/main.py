import asyncio
from nv200_driver import DeviceClient, PidLoopMode, StatusFlags, TelnetProtocol, SerialProtocol
from data_recorder import DataRecorderSource, RecorderAutoStartMode, DataRecorder


async def basic_tests(client: DeviceClient):
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


async def data_recorder_tests(client: DeviceClient):
    recorder = DataRecorder(client)
    # await recorder.set_data_source(1, DataRecorderSource.PIEZO_POSITION)
    # await recorder.set_autostart_mode(RecorderAutoStartMode.START_ON_SET_COMMAND)
    # await recorder.set_recorder_stride(1)
    # await recorder.start_recording()
    #data = await recorder.read_recorded_data(0)
    #print("Data: " , data) 
    await recorder.set_recording_duration(308)
    # await data_recorder.set_data_source(1, DataRecorderSource.SETPOINT)
    # await data_recorder.set_data_source(2, DataRecorderSource.PIEZO_VOLTAGE)
    # await data_recorder.set_data_source(3, DataRecorderSource.POSITION_ERROR)
    # await data_recorder.set_data_source(4, DataRecorderSource.ABS_POSITION_ERROR)
    # await data_recorder.set_data_source(5, DataRecorderSource.PIEZO_CURRENT_1)
    # await data_recorder.set_data_source(6, DataRecorderSource.PIEZO_CURRENT_2)
    # await data_recorder.set_autostart_mode(RecorderAutoStartMode.START_ON_SET_COMMAND)
    # await data_recorder.set_recording_interval(1000)
    # await data_recorder.set_recording_duration(10000)
    # await data_recorder.start_recording()
    # await asyncio.sleep(10)
    # await data_recorder.stop_recording()
    # await data_recorder.download_data("data.csv")



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
