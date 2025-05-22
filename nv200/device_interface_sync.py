"""
Auto-generated sync wrapper for `device_interface`.

This module provides synchronous wrappers for async and sync functions and classes.
"""

import device_interface
from syncwrap import run as _run


def create_device_client(detected_device):
    """
    Factory function to create a DeviceClient with the right transport protocol 
    from a DetectedDevice.
    This function determines the appropriate transport protocol
    based on the detected device type (e.g., serial or telnet) and returns a 
    properly configured DeviceClient instance.
    """
    return device_interface.create_device_client(detected_device)


class DeviceClient:
    def __init__(self, *args, **kwargs):
        self._inner = device_interface.DeviceClient(*args, **kwargs)


    def serial_protocol(self, ):
        """
        Returns the transport as SerialProtocol or raises TypeError.

        Returns:
            SerialProtocol: The transport instance as SerialProtocol.
        """
        return self._inner.serial_protocol()


    def ethernet_protocol(self, ):
        """
        Returns the transport as TelnetProtocol or raises TypeError.
        """
        return self._inner.ethernet_protocol()


    def connect(self, auto_adjust_comm_params):
        """
        Establishes a connection using the transport layer.

        This asynchronous method initiates the connection process by calling
        the `connect` method of the transport instance.

        Raises:
            Exception: If the connection fails, an exception may be raised
                       depending on the implementation of the transport layer.
        """
        return _run(self._inner.connect(auto_adjust_comm_params))


    def write(self, cmd):
        """
        Sends a command to the transport layer.

        This asynchronous method writes a command string followed by a carriage return
        to the transport layer.

        Args:
            cmd (str): The command string to be sent. No carriage return is needed. 

        Example:
            >>> await device_client.write('set,80')
        """
        return _run(self._inner.write(cmd))


    def read(self, cmd, timeout):
        """
        Sends a command to the transport layer and reads the response asynchronously.
        For example, if you write `cl` to the device, it will return `cl,0` or `cl,1`
        depending on the current PID mode. That means, this function returns the
        complete string ``cl,0\r\n`` or ``cl,1\r\n`` including the carriage return and line feed.

        Args:
            cmd (str): The command string to be sent.
            timeout: The timeout for reading the response in seconds.

        Returns:
            str: The response received from the transport layer.

        Example: 
            >>> response = await device_client.read('cl')
            >>> print(response)
            b'cl,1\r\n'
        """
        return _run(self._inner.read(cmd, timeout))


    def read_response(self, cmd, timeout):
        """
        Asynchronously sends a command to read values and parses the response.
        For example, if you write the command `set`, it will return `set,80.000` if
        the setpoint is 80.000. The response is parsed into a tuple containing the command `set`
        and a list of parameter strings, in this case `[80.000]`.

        Args:
            cmd (str): The command string to be sent.

        Returns:
            tuple: A tuple containing the command (str) and a list of parameters (list of str).

        Example:
            >>> response = await device_client.read_response('set')
            >>> print(response)
            ('set', ['80.000'])
        """
        return _run(self._inner.read_response(cmd, timeout))


    def read_values(self, cmd, timeout):
        """
        Asynchronously sends a command and returns the values as a list of strings.
        For example, if you write the command `'recout,0,0,1`, to read the first data recorder
        value, it will return `['0', '0', '0.029']` if the first data recorder value is `0.029`.
        So it returns a list of 3 strings.

        Args:
            cmd (str): The command string to be sent.

        Returns:
            A list of values (list of str)..

        Example:
            >>> values = await device_client.read_values('recout,0,0,1')
            >>> print(values)
            ['0', '0', '0.029']
        """
        return _run(self._inner.read_values(cmd, timeout))


    def read_float_value(self, cmd, param_index):
        """
        Asynchronously reads a single float value from device.
        For example, if you write the command `set`, to read the current setpoint,
        it will return `80.000` if the setpoint is 80.000. The response is parsed into a
        float value. Use this function for command that returns a single floating point value.

        Args:
            cmd (str): The command string to be sent.
            param_index (int): Parameter index (default 0) to read from the response.

        Returns:
            float: The value as a floating-point number.

        Example:
            >>> value = await device_client.read_float_value('set')
            >>> print(value)
            80.000
        """
        return _run(self._inner.read_float_value(cmd, param_index))


    def read_int_value(self, cmd, param_index):
        """
        Asynchronously reads a single float value from device.
        For example, if you write `cl` to the device, the response will be `0` or `1`
        depending on the current PID mode. The response is parsed into an integer value.

        Args:
            cmd (str): The command string to be sent.
            param_index (int): Parameter index (default 0) to read from the response

        Returns:
            float: The value as a floating-point number.

        Example:
            >>> value = await device_client.read_int_value('cl')
            >>> print(value)
            1
        """
        return _run(self._inner.read_int_value(cmd, param_index))


    def read_string_value(self, cmd, param_index):
        """
        Asynchronously reads a single string value from device.
        For example, if you write the command `desc`, the device will return
        the name of the actuator i.e. `TRITOR100SG` . The response is parsed 
        into a string value.

        Args:
            cmd (str): The command string to be sent.
            param_index (int): Parameter index (default 0) to read from the response.

        Returns:
            str: The value as a string.

        Example:
            >>> await self.read_string_value('desc')
            >>> print(value)
            TRITOR100SG
        """
        return _run(self._inner.read_string_value(cmd, param_index))


    def close(self, ):
        """
        Asynchronously closes the transport connection.

        This method ensures that the transport layer is properly closed,
        releasing any resources associated with it.
        """
        return _run(self._inner.close())


    def set_pid_mode(self, mode):
        """
        Sets the PID mode of the device to either open loop or closed loop.
        """
        return _run(self._inner.set_pid_mode(mode))


    def get_pid_mode(self, ):
        """
        Retrieves the current PID mode of the device.
        """
        return _run(self._inner.get_pid_mode())


    def set_modulation_source(self, source):
        """
        Sets the setpoint modulation source.
        """
        return _run(self._inner.set_modulation_source(source))


    def get_modulation_source(self, ):
        """
        Retrieves the current setpoint modulation source.
        """
        return _run(self._inner.get_modulation_source())


    def set_setpoint(self, setpoint):
        """
        Sets the setpoint value for the device.
        """
        return _run(self._inner.set_setpoint(setpoint))


    def get_setpoint(self, ):
        """
        Retrieves the current setpoint of the device.
        """
        return _run(self._inner.get_setpoint())


    def move_to_position(self, position):
        """
        Moves the device to the specified position in closed loop
        """
        return _run(self._inner.move_to_position(position))


    def move_to_voltage(self, voltage):
        """
        Moves the device to the specified voltage in open loop
        """
        return _run(self._inner.move_to_voltage(voltage))


    def move(self, target):
        """
        Moves the device to the specified target position or voltage.
        The target is interpreted as a position in closed loop or a voltage in open loop.
        """
        return _run(self._inner.move(target))


    def get_current_position(self, ):
        """
        Retrieves the current position of the device.
        For actuators with sensor: Position in actuator units (μm or mrad)
        For actuators without sensor: Piezo voltage in V
        """
        return _run(self._inner.get_current_position())


    def get_heat_sink_temperature(self, ):
        """
        Retrieves the heat sink temperature in degrees Celsius.
        """
        return _run(self._inner.get_heat_sink_temperature())


    def get_status_register(self, ):
        """
        Retrieves the status register of the device.
        """
        return _run(self._inner.get_status_register())


    def is_status_flag_set(self, flag):
        """
        Checks if a specific status flag is set in the status register.
        """
        return _run(self._inner.is_status_flag_set(flag))


    def get_actuator_name(self, ):
        """
        Retrieves the name of the actuator that is connected to the NV200 device.
        """
        return _run(self._inner.get_actuator_name())


    def get_actuator_serial_number(self, ):
        """
        Retrieves the serial number of the actuator that is connected to the NV200 device.
        """
        return _run(self._inner.get_actuator_serial_number())


    def get_actuator_description(self, ):
        """
        Retrieves the description of the actuator that is connected to the NV200 device.
        The description consists of the actuator type and the serial number.
        For example: "TRITOR100SG, #85533"
        """
        return _run(self._inner.get_actuator_description())


    def get_device_type(self, ):
        """
        Retrieves the type of the device.
        The device type is the string that is returned if you just press enter after connecting to the device.
        """
        return _run(self._inner.get_device_type())


    def get_slew_rate(self, ):
        """
        Retrieves the slew rate of the device.
        The slew rate is the maximum speed at which the device can move.
        """
        return _run(self._inner.get_slew_rate())


    def set_slew_rate(self, slew_rate):
        """
        Sets the slew rate of the device.
        0.0000008 ... 2000.0 %ms⁄ (2000 = disabled)
        """
        return _run(self._inner.set_slew_rate(slew_rate))


    def enable_setpoint_lowpass_filter(self, enable):
        """
        Enables the low-pass filter for the setpoint.
        """
        return _run(self._inner.enable_setpoint_lowpass_filter(enable))


    def is_setpoint_lowpass_filter_enabled(self, ):
        """
        Checks if the low-pass filter for the setpoint is enabled.
        """
        return _run(self._inner.is_setpoint_lowpass_filter_enabled())


    def set_setpoint_lowpass_filter_cutoff_freq(self, frequency):
        """
        Sets the cutoff frequency of the low-pass filter for the setpoint from 1..10000 Hz.
        """
        return _run(self._inner.set_setpoint_lowpass_filter_cutoff_freq(frequency))


    def get_setpoint_lowpass_filter_cutoff_freq(self, ):
        """
        Retrieves the cutoff frequency of the low-pass filter for the setpoint.
        """
        return _run(self._inner.get_setpoint_lowpass_filter_cutoff_freq())
