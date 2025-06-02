from nv200.device_base import PiezoDeviceBase
from nv200.shared_types import PidLoopMode, ModulationSource, StatusRegister, StatusFlags, DetectedDevice, TransportType
from nv200.telnet_protocol import TelnetProtocol
from nv200.serial_protocol import SerialProtocol



class NV200Device(PiezoDeviceBase):
    """
    A high-level asynchronous client for communicating with NV200 piezo controllers.
    This class extends the `PiezoController` base class and provides high-level methods
    for setting and getting various device parameters, such as PID mode, setpoint,
    """
    DEVICE_ID = "NV200/D_NET"

    async def enrich_device_info(self, detected_device : DetectedDevice) -> None :
        """
        Get additional information about the device.

        A derived class should implement this method to enrich the device information in the given
        detected_device object.

        Args:
            detected_device (DetectedDevice): The detected device object to enrich with additional information.
        """
        detected_device.actuator_name = await self.get_actuator_name()
        detected_device.actuator_serial = await self.get_actuator_serial_number()

    async def set_pid_mode(self, mode: PidLoopMode):
        """Sets the PID mode of the device to either open loop or closed loop."""
        await self.write(f"cl,{mode.value}")

    async def get_pid_mode(self) -> PidLoopMode:
        """Retrieves the current PID mode of the device."""
        return PidLoopMode(await self.read_int_value('cl'))
    
    async def set_modulation_source(self, source: ModulationSource):
        """Sets the setpoint modulation source."""
        await self.write(f"modsrc,{source.value}")

    async def get_modulation_source(self) -> ModulationSource:
        """Retrieves the current setpoint modulation source."""
        return ModulationSource(await self.read_int_value('modsrc'))
    
    async def set_setpoint(self, setpoint: float):
        """Sets the setpoint value for the device."""
        await self.write(f"set,{setpoint}")

    async def get_setpoint(self) -> float:
        """Retrieves the current setpoint of the device."""
        return await self.read_float_value('set')
    
    async def move_to_position(self, position: float):
        """Moves the device to the specified position in closed loop"""
        await self.set_pid_mode(PidLoopMode.CLOSED_LOOP)
        await self.set_setpoint(position)

    async def move_to_voltage(self, voltage: float):
        """Moves the device to the specified voltage in open loop"""
        await self.set_pid_mode(PidLoopMode.OPEN_LOOP)
        await self.set_setpoint(voltage)

    async def move(self, target: float):
        """
        Moves the device to the specified target position or voltage.
        The target is interpreted as a position in closed loop or a voltage in open loop.
        """
        await self.set_setpoint(target)

    async def get_current_position(self) -> float:
        """
        Retrieves the current position of the device.
        For actuators with sensor: Position in actuator units (μm or mrad)
        For actuators without sensor: Piezo voltage in V
        """
        return await self.read_float_value('meas')

    async def get_heat_sink_temperature(self) -> float:
        """
        Retrieves the heat sink temperature in degrees Celsius.
        """
        return await self.read_float_value('temp')

    async def get_status_register(self) -> StatusRegister:
        """
        Retrieves the status register of the device.
        """
        return StatusRegister(await self.read_int_value('stat'))

    async def is_status_flag_set(self, flag: StatusFlags) -> bool:
        """
        Checks if a specific status flag is set in the status register.
        """
        status_reg = await self.get_status_register()
        return status_reg.has_flag(flag)
    
    async def get_actuator_name(self) -> str:
        """
        Retrieves the name of the actuator that is connected to the NV200 device.
        """
        return await self.read_string_value('desc')
    
    async def get_actuator_serial_number(self) -> str:
        """
        Retrieves the serial number of the actuator that is connected to the NV200 device.
        """
        return await self.read_string_value('acserno')
    
    async def get_actuator_description(self) -> str:
        """
        Retrieves the description of the actuator that is connected to the NV200 device.
        The description consists of the actuator type and the serial number.
        For example: "TRITOR100SG, #85533"
        """
        name = await self.get_actuator_name()
        serial_number = await self.get_actuator_serial_number()   
        return f"{name} #{serial_number}"
    
    async def get_slew_rate(self) -> float:
        """
        Retrieves the slew rate of the device.
        The slew rate is the maximum speed at which the device can move.
        """
        return await self.read_float_value('sr')
    
    async def set_slew_rate(self, slew_rate: float):
        """
        Sets the slew rate of the device.
        0.0000008 ... 2000.0 %ms⁄ (2000 = disabled)
        """
        async with self.lock:
            await self.write(f"sr,{slew_rate}")

    async def enable_setpoint_lowpass_filter(self, enable: bool):
        """
        Enables the low-pass filter for the setpoint.
        """
        await self.write(f"setlpon,{int(enable)}")

    async def is_setpoint_lowpass_filter_enabled(self) -> bool:
        """
        Checks if the low-pass filter for the setpoint is enabled.
        """
        return await self.read_int_value('setlpon') == 1
    
    async def set_setpoint_lowpass_filter_cutoff_freq(self, frequency: int):
        """
        Sets the cutoff frequency of the low-pass filter for the setpoint from 1..10000 Hz.
        """
        await self.write(f"setlpf,{frequency}")

    async def get_setpoint_lowpass_filter_cutoff_freq(self) -> int:
        """
        Retrieves the cutoff frequency of the low-pass filter for the setpoint.
        """
        return await self.read_int_value('setlpf')

    @staticmethod
    def from_detected_device(detected_device: DetectedDevice) -> "NV200Device":
        """
        Creates an NV200Device instance from a DetectedDevice object by selecting the appropriate
        transport protocol based on the detected device's transport type.
        Args:
            detected_device (DetectedDevice): The detected device containing transport type and identifier.
        Returns:
            NV200Device: An instance of NV200Device initialized with the correct transport protocol.
        """
        if detected_device.transport == TransportType.TELNET:
            transport = TelnetProtocol(host = detected_device.identifier)
        elif detected_device.transport == TransportType.SERIAL:
            transport = SerialProtocol(port = detected_device.identifier)
        else:
            raise ValueError(f"Unsupported transport type: {detected_device.transport}")
        
        # Return a DeviceClient initialized with the correct transport protocol
        return NV200Device(transport)