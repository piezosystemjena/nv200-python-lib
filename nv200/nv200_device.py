from typing import Dict, Tuple, TYPE_CHECKING
import os
import configparser
from nv200.device_base import PiezoDeviceBase
from nv200.shared_types import (
    PidLoopMode,
    ModulationSource,
    StatusRegister,
    StatusFlags,
    DetectedDevice,
    TransportType,
    AnalogMonitorSource,
    SPIMonitorSource,
    PIDGains,
    PCFGains,
    CtrlMode,
    ValueRange,
    PostionSensorType
)
from nv200.telnet_protocol import TelnetProtocol
from nv200.serial_protocol import SerialProtocol
from nv200.transport_protocol import TransportProtocol

if TYPE_CHECKING:
    # For forward reference of NV200Device within inner classes
    from typing import Any


class NV200Device(PiezoDeviceBase):
    """
    A high-level asynchronous client for communicating with NV200 piezo controllers.

    This class extends the `PiezoDeviceBase` base class and provides high-level methods
    for setting and getting various device parameters, such as PID mode, setpoint, etc.

    Attributes:
        setpoint_lpf (NV200Device.LowpassFilter): Interface for the setpoint low-pass filter.
        position_lpf (NV200Device.LowpassFilter): Interface for the position low-pass filter.
        notch_filter (NV200Device.NotchFilter): Interface for the notch filter.
        pid (NV200Device.PIDController): Interface for the PID controller to set the controller mode and PID gains.
    """
    DEVICE_ID = "NV200/D_NET"
    CACHEABLE_COMMANDS = {
        "cl",
        "ctrlmode",
        "unitcl",
        "unitol",
        "avmin",
        "avmax",
        "posmin",
        "posmax",
        "modsrc",
        "monsrc",
        "spisrc",
        "sr",
        "kp",
        "ki",
        "kd",
        "setlpf",
        "setlpon",
        "poslpf",
        "poslpon"
        "notchf",
        "notchon",
        "notchb",
        "acmeasure"
    }
    _help_dict: dict[str, str] = {
        # General Commands
        "s": "Print full command list",
        "reset": "Hardware-reset of the controller",
        "fenable": "Enable/disable full range voltage sweep during power-up (0=disabled, 1=enabled)",
        "sinit": "Set initial actuator position after power-up (0 to 100 %)",
        "set": "Setpoint: voltage (open loop) or position (closed loop), range limited by actuator",
        "setst": "Smooth setpoint: setst,<value1>=Setpoint,<value2>=JumpTime; same rules as 'set'",
        "meas": "Read position (with sensor) or piezo voltage (no sensor)",
        "imeas": "Read measured piezo current (0=channel 1, 1=channel 2)",
        "ctrlmode": "Controller mode (0=PID, 1=ILC identification, 2=ILC feedforward, 3=ILC feedback)",
        "temp": "Read heat sink temperature",
        "stat": "Read status register",
        "posmin": "Lower motion range limit",
        "posmax": "Upper motion range limit",
        "avmin": "Lower voltage range limit",
        "avmax": "Upper voltage range limit",
        "modsrc": "Setpoint source (0=USB/Ethernet, 1=Analog In, 2=SPI, 3=AWG)",
        "monsrc": (
            "Analog output source (0=position closed loop, 1=setpoint, 2=piezo voltage, "
            "3=position error, 4=abs(position error), 5=position open loop, 6=piezo current 1, 7=piezo current 2)"
        ),

        # actuator information
        "desc": "Actuator description (type such as 'TRITOR100SG')",
        "acserno": "Actuator serial number",
        "acmeasure": "Actuator position sensor type (0=none, 1=straingauge, 2=capacitive, 3=LVDT)",

        # PID and Filters
        "cl": "Loop mode (0=open loop, 1=closed loop)",
        "sr": "Slew rate limit (0.0000008 to 2000.0 %/ms; 2000=disabled)",
        "kp": "PID proportional gain (0 to 10000)",
        "ki": "PID integral gain (0 to 10000)",
        "kd": "PID differential gain (0 to 10000)",
        "tf": "PID differential term (time constant)",
        "pcf": (
            "PID feedforward gain: pcf,<position_gain>,<velocity_gain>,<acceleration_gain> "
            "(acceleration scaled internally by 1/1,000,000)"
        ),
        "setlpon": "Enable/disable setpoint lowpass filter (0=off, 1=on)",
        "setlpf": "Setpoint lowpass cutoff frequency (1 to 10000 Hz)",
        "notchon": "Enable/disable notch filter (0=off, 1=on)",
        "notchf": "Notch filter frequency (1 to 10000 Hz)",
        "notchb": "Notch filter bandwidth (-3dB) (1 to 10000 Hz; max = 2 * notchf)",
        "poslpon": "Enable/disable position lowpass filter (0=off, 1=on)",
        "poslpf": "Position lowpass cutoff frequency (1 to 10000 Hz)",

        # Arbitrary Waveform Generator
        "grun": "Start/stop AWG (0=stop, 1=start)",
        "gsarb": "AWG start index (0 to 1023)",
        "gearb": "AWG end index (0 to 1023)",
        "gcarb": "AWG cycles (0=infinite, 1 to 65535)",
        "goarb": "AWG offset index (0 to 1023)",
        "giarb": "Read current AWG index",
        "gtarb": "Output sampling factor (1 to 65535; sample time = factor * 50µs)",
        "gbarb": "Write AWG buffer in % units (index: 0 to 1023, value: 0.0 to 100.0)",
        "gparb": "Write AWG buffer in length units (index: 0 to 1023, value: posmin to posmax)",
        "gsave": "Save AWG buffer to EEPROM",
        "gload": "Load AWG buffer from EEPROM",

        # Data Recorder
        "recsrc": (
            "Set data recorder source: recsrc,<ch>,<src>; ch: 0=A, 1=B; "
            "src: 0=position, 1=setpoint, 2=voltage, 3=error, 4=abs(error), "
            "5=position (open loop), 6=piezo current 1, 7=piezo current 2"
        ),
        "recast": "Recorder autostart (0=off, 1=start on set, 2=start on grun)",
        "recstr": "Recorder stride (store every nth value) (1 to 65535)",
        "reclen": "Recorder length (0 to 6144; 0=infinite loop)",
        "recrun": "Start/stop recorder (0=stop, 1=start)",
        "recidx": "Read current recorder write index",
        "recout": "Read recorder by index: recout,<ch>,<index>,<value>",
        "recoutf": "Read full recorder buffer (comma-separated)",

        # Trigger In
        "trgfkt": (
            "Trigger input function (0=none, 1=AWG start, 2=AWG step, 3=AWG sync, "
            "4=ILC sync, 5=recorder start)"
        ),

        # Trigger Out
        "trgedg": "Trigger edge mode (0=off, 1=rising, 2=falling, 3=both)",
        "trgsrc": "Trigger signal source (0=position, 1=setpoint)",
        "trgss": "Trigger start position (posmin+0.001 to posmax-0.001)",
        "trgse": "Trigger stop position (posmin+0.001 to posmax-0.001)",
        "trgsi": "Trigger step size (0.001 to posmax-0.001)",
        "trglen": "Trigger pulse length in samples (0 to 255, time = length * 50µs)",

        # SPI
        "spisrc": (
            "SPI return source (0=0x0000, 1=position, 2=setpoint, 3=voltage, 4=error, "
            "5=abs(error), 6=position open loop, 7=piezo current 1, 8=piezo current 2, 9=test 0x5A5A)"
        ),
        "spitrg": "SPI interrupt source (0=internal, 1=SPI)",
        "spis": "SPI setpoint format (0=hex, 1=decimal, 2=stroke/voltage)",

        # ILC
        "idata": "Read all ILC parameters",
        "iemin": "ILC lower error threshold 'emin' (0.0001 to 1.0)",
        "irho": "ILC learning rate 'rho' (0.0001 to 1.0)",
        "in0": "Number of basic scans (≥ in1) (2 to 65535)",
        "in1": "Number of subsamples (power of 2: 2, 4, 8...1024)",
        "inx": "Frequency components to learn (1 to 128, must be < ½ * in1)",
        "iut": "Read piezo voltage profile (time domain)",
        "iyt": "Read measured position profile (time domain)",
        "ii1t": "Read piezo current channel 1 (time domain)",
        "ii2t": "Read piezo current channel 2 (time domain)",
        "igc": "Read learning function (frequency domain)",
        "iuc": "Read piezo voltage profile (frequency domain)",
        "iwc": (
            "Set/read desired position profile (frequency domain): "
            "iwc,<index>,<real>,<imag>; index: 0 to inx"
        ),
        "iyc": "Read measured position profile (frequency domain)",
        "igt": "Correction mode (0=no learning, 1=offline ID, 2=online ID)",
        "isave": "Save ILC learning profiles to actuator",
        "iload": "Load ILC learning profiles from actuator",
    }

    class LowpassFilter:
        """
        Interface to a low-pass filter configuration on the NV200 device.

        This class is parameterized by the command strings for enabling the filter and
        setting/getting the cutoff frequency.
        """

        def __init__(self, device: "NV200Device", enable_cmd: str, cutoff_cmd: str, cutoff_range: ValueRange[float]) -> None:
            """
            Initialize the LowpassFilter.

            Args:
                device (NV200Device): The parent device instance.
                enable_cmd (str): The device command to enable/disable the filter.
                cutoff_cmd (str): The device command to set/get the cutoff frequency.
            """
            self._device = device
            self._enable_cmd = enable_cmd
            self._cutoff_cmd = cutoff_cmd
            self.cutoff_range = cutoff_range

        async def enable(self, enable: bool) -> None:
            """
            Enable or disable the low-pass filter.

            Args:
                enable (bool): True to enable, False to disable.
            """
            await self._device.write_value(self._enable_cmd, int(enable))

        async def is_enabled(self) -> bool:
            """
            Check if the low-pass filter is enabled.

            Returns:
                bool: True if enabled, False otherwise.
            """
            return await self._device.read_int_value(self._enable_cmd) == 1

        async def set_cutoff(self, frequency: float) -> None:
            """
            Set the cutoff frequency of the low-pass filter.

            Args:
                frequency (int): The cutoff frequency in Hz (valid range 1..10000).
            """
            await self._device.write_value(self._cutoff_cmd, frequency)

        async def get_cutoff(self) -> float:
            """
            Get the cutoff frequency of the low-pass filter.

            Returns:
                int: The cutoff frequency in Hz.
            """
            return await self._device.read_float_value(self._cutoff_cmd)
        

    class NotchFilter:
        """
        Interface to a notch filter configuration on the NV200 device.

        Allows enabling/disabling the notch filter and configuring its
        center frequency and -3 dB bandwidth.
        """

        def __init__(self, device: "NV200Device") -> None:
            """
            Initialize the NotchFilter interface.

            Args:
                device (NV200Device): The parent device instance used for communication.
            """
            self._device = device
            self.freq_range : ValueRange[int] = ValueRange(1, 10000)  # Valid range for notch frequency
            self.bandwidth_range : ValueRange[int] = ValueRange(1, 10000)  # Valid range for notch bandwidth

        async def enable(self, enable: bool) -> None:
            """
            Enable or disable the notch filter.

            Args:
                enable (bool): True to enable the filter, False to disable.
            """
            await self._device.write_value("notchon", int(enable))

        async def is_enabled(self) -> bool:
            """
            Check if the notch filter is currently enabled.

            Returns:
                bool: True if the filter is enabled, False otherwise.
            """
            return await self._device.read_int_value("notchon") == 1

        async def set_frequency(self, frequency: int) -> None:
            """
            Set the center frequency of the notch filter.

            Args:
                frequency (int): Center frequency in Hz. Valid range is 1 to 10,000 Hz.
            """
            await self._device.write_value("notchf", frequency)

        async def get_frequency(self) -> int:
            """
            Get the center frequency of the notch filter.

            Returns:
                int: Current center frequency in Hz.
            """
            return await self._device.read_int_value("notchf")

        async def set_bandwidth(self, bandwidth: int) -> None:
            """
            Set the -3 dB bandwidth of the notch filter.

            Args:
                bandwidth (int): Bandwidth in Hz. Valid range is 1 to 10,000 Hz,
                                but must not exceed 2 × center frequency.
            """
            await self._device.write_value("notchb", bandwidth)

        async def get_bandwidth(self) -> int:
            """
            Get the -3 dB bandwidth of the notch filter.

            Returns:
                int: Current bandwidth in Hz.
            """
            return await self._device.read_int_value("notchb")
        

    class PIDController:
        """
        PIDController provides an interface for configuring and controlling the PID control loop of an NV200 device.
        This class allows enabling/disabling closed loop control, setting and retrieving PID gains, and 
        configuring feed-forward control amplification factors for position, velocity, and acceleration.
        """
        
        def __init__(self, device: "NV200Device") -> None:
            """
            Initialize the NotchFilter interface.

            Args:
                device (NV200Device): The parent device instance used for communication.
            """
            self._device = device


        async def set_closed_loop(self, enable: bool) -> None:
            """
            Enable or disable closed loop control mode.
            """
            await self.set_mode(PidLoopMode.CLOSED_LOOP if enable else PidLoopMode.OPEN_LOOP)

        async def is_closed_loop(self) -> bool:
            """
            Check if the device is currently in closed loop control mode.
            Returns:
                bool: True if in closed loop mode, False otherwise.
            """
            return await self.get_mode() == PidLoopMode.CLOSED_LOOP

        async def set_mode(self, mode: PidLoopMode):
            """Sets the PID mode of the device to either open loop or closed loop."""
            await self._device.write_value('cl', mode.value)

        async def get_mode(self) -> PidLoopMode:
            """Retrieves the current PID mode of the device."""
            return PidLoopMode(await self._device.read_int_value('cl'))
        

        async def set_pid_gains(self, kp: float | None = None, ki: float | None = None, kd: float | None = None) -> None:
            """
            Sets the PID gains for the device.
            """
            dev = self._device
            if kp is not None:
                await dev.write_value("kp", kp)
            if ki is not None:
                await dev.write_value("ki", ki)
            if kd is not None:
                await dev.write_value("kd", kd)


        async def get_pid_gains(self) -> PIDGains:
            """
            Retrieves the PID gains (kp, ki, kd) for the device.

            Returns:
                PIDGains: A named tuple with fields kp, ki, and kd.
            """
            dev = self._device
            kp = await dev.read_float_value('kp')
            ki = await dev.read_float_value('ki')
            kd = await dev.read_float_value('kd')
            return PIDGains(kp, ki, kd)
        

        async def set_pcf_gains(
            self,
            position: float | None = None,
            velocity: float | None = None,
            acceleration: float | None = None,
        ) -> None:
            """
            Sets the PID controllers feed forward control amplification factors.

            Args:
                position (float | None): Factor for position feed-forward. Leave unchanged if None.
                velocity (float | None): Factor for velocity feed-forward. Leave unchanged if None.
                acceleration (float | None): Factor for acceleration feed-forward (scaled by 1/1_000_000 internally). Leave unchanged if None.
            """
            # Read existing values if any factor is None to preserve them
            if None in (position, velocity, acceleration):
                current = await self.get_pcf_gains()

            pcf_x = position if position is not None else current.position
            pcf_v = velocity if velocity is not None else current.velocity
            # Scale acceleration before sending command
            pcf_a = int(acceleration * 1_000_000) if acceleration is not None else int(current.acceleration * 1_000_000)

            # Compose the command string (assuming a single write command)
            command_value = f"{pcf_x},{pcf_v},{pcf_a}"
            await self._device.write_value("pcf", command_value)


        async def get_pcf_gains(self) -> PCFGains:
            """
            Retrieves the feed forward control amplification factors.

            Returns:
                PCFGains: The feed forward factors for position, velocity, and acceleration.
            """
            # Assume read_value returns the string "<pcf_x>,<pcf_v>,<pcf_a>"
            raw = await self._device.read_cached_response_parameters_tring('pcf')
            pcf_x_str, pcf_v_str, pcf_a_str = raw.split(",")
            pcf_x = float(pcf_x_str)
            pcf_v = float(pcf_v_str)
            pcf_a = float(pcf_a_str) / 1_000_000  # scale back

            return PCFGains(position=pcf_x, velocity=pcf_v, acceleration=pcf_a)
        

    def __init__(self, transport: TransportProtocol):
        """
        Initialize NV200Device and its low-pass filter interfaces.
        """
        super().__init__(transport)  # call base class constructor
        self.setpoint_lpf = self.LowpassFilter(self, "setlpon", "setlpf", ValueRange(1, 10000))
        self.position_lpf = self.LowpassFilter(self, "poslpon", "poslpf", ValueRange(100, 10000))
        self.notch_filter = self.NotchFilter(self)
        self.pid = self.PIDController(self)


    async def enrich_device_info(self, detected_device : DetectedDevice) -> None :
        """
        Get additional information about the device.

        A derived class should implement this method to enrich the device information in the given
        detected_device object.

        Args:
            detected_device (DetectedDevice): The detected device object to enrich with additional information.
        """
        detected_device.device_info.clear()
        detected_device.device_info['actuator_name'] = await self.get_actuator_name()
        detected_device.device_info['actuator_serial'] = await self.get_actuator_serial_number()

    
    async def set_modulation_source(self, source: ModulationSource):
        """Sets the setpoint modulation source."""
        await self.write_value("modsrc", source.value)

    async def get_modulation_source(self) -> ModulationSource:
        """Retrieves the current setpoint modulation source."""
        return ModulationSource(await self.read_int_value('modsrc'))
    
    async def set_spi_monitor_source(self, source: SPIMonitorSource):
        """Sets the source for the SPI/Monitor value returned via SPI MISO."""
        await self.write_value("spisrc", source.value)

    async def get_spi_monitor_source(self) -> SPIMonitorSource:
        """Returns the source for the SPI/Monitor value returned via SPI MISO."""
        return SPIMonitorSource(await self.read_int_value('spisrc'))
    
    async def set_analog_monitor_source(self, source: AnalogMonitorSource):
        """Sets the source of data for analog output (monsrc)."""
        await self.write_value("monsrc", source.value)

    async def get_analog_monitor_source(self) -> AnalogMonitorSource:
        """Returns the source of data for analog output (monsrc)."""
        return AnalogMonitorSource(await self.read_int_value('monsrc'))
    
    async def set_setpoint(self, setpoint: float):
        """Sets the setpoint value for the device."""
        await self.write_value("set", setpoint)

    async def get_setpoint(self) -> float:
        """Retrieves the current setpoint of the device."""
        return await self.read_float_value('set')
    
    async def move_to_position(self, position: float):
        """Moves the device to the specified position in closed loop"""
        await self.pid.set_mode(PidLoopMode.CLOSED_LOOP)
        await self.set_modulation_source(ModulationSource.SET_CMD)
        await self.set_setpoint(position)

    async def move_to_voltage(self, voltage: float):
        """Moves the device to the specified voltage in open loop"""
        await self.pid.set_mode(PidLoopMode.OPEN_LOOP)
        await self.set_modulation_source(ModulationSource.SET_CMD)
        await self.set_setpoint(voltage)

    async def move(self, target: float):
        """
        Moves the device to the specified target position or voltage.
        The target is interpreted as a position in closed loop or a voltage in open loop.
        """
        await self.set_modulation_source(ModulationSource.SET_CMD)
        await self.set_setpoint(target)

    async def get_current_position(self) -> float:
        """
        Retrieves the current position of the device.
        For actuators with sensor: Position in actuator units (μm or mrad)
        For actuators without sensor: Piezo voltage in V
        """
        return await self.read_float_value('meas')
    
    async def get_max_position(self) -> float:
        """
        Retrieves the maximum position of the device.
        For actuators with sensor: Maximum position in actuator units (μm or mrad)
        For actuators without sensor: Maximum piezo voltage in V
        """
        return await self.read_float_value('posmax')
    
    async def get_min_position(self) -> float:
        """
        Retrieves the minimum position of the device.
        For actuators with sensor: Minimum position in actuator units (μm or mrad)
        For actuators without sensor: Minimum piezo voltage in V
        """
        return await self.read_float_value('posmin')
    
    async def get_position_range(self) -> Tuple[float, float]:
        """
        Retrieves the position range of the device for closed loop control.
        Returns a tuple containing the minimum and maximum position.
        """
        min_pos = await self.get_min_position()
        max_pos = await self.get_max_position()
        return (min_pos, max_pos)
    
    async def get_max_voltage(self) -> float:
        """
        Retrieves the maximum voltage of the device.
        This is the maximum voltage that can be applied to the piezo actuator.
        """
        return await self.read_float_value('avmax')
    
    async def get_min_voltage(self) -> float:
        """
        Retrieves the minimum voltage of the device.
        This is the minimum voltage that can be applied to the piezo actuator.
        """
        return await self.read_float_value('avmin')
    
    async def get_voltage_range(self) -> Tuple[float, float]:
        """
        Retrieves the voltage range of the device for open loop control.
        Returns a tuple containing the minimum and maximum voltage.
        """
        min_voltage = await self.get_min_voltage()
        max_voltage = await self.get_max_voltage()
        return (min_voltage, max_voltage)
    
    async def get_setpoint_range(self) -> Tuple[float, float]:
        """
        Retrieves the setpoint range of the device.
        Returns a tuple containing the minimum and maximum setpoint.
        The setpoint range is determined by the position range for closed loop control
        and the voltage range for open loop control.
        """
        if await self.pid.get_mode() == PidLoopMode.CLOSED_LOOP:
            return await self.get_position_range()
        else:
            return await self.get_voltage_range()
        
    async def get_voltage_unit(self) -> str:
        """
        Retrieves the voltage unit of the device.
        This is typically "V" for volts.
        """
        return await self.read_string_value('unitol')
    
    async def get_position_unit(self) -> str:
        """
        Retrieves the position unit of the device.
        This is typically "μm" for micrometers for linear actuatros or "mrad" for 
        milliradians for tilting actuators.
        """
        return await self.read_string_value('unitcl')
    
    async def get_setpoint_unit(self) -> str:
        """
        Retrieves the current setpoint unit of the device.
        This is typically "V" for volts in open loop or the position unit in closed loop.
        """
        if await self.pid.get_mode() == PidLoopMode.CLOSED_LOOP:
            return await self.get_position_unit()
        else:
            return await self.get_voltage_unit()

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
    
    async def get_actuator_sensor_type(self) -> PostionSensorType:
        """
        Retrieves the type of position sensor used by the actuator.
        Returns a PostionSensorType enum value.
        """
        sensor_type_value = await self.read_int_value('acmeasure')
        return PostionSensorType(sensor_type_value)
    
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
            await self.write_value("sr", slew_rate)
    

    async def export_actuator_config(self, path : str = "", filename: str = "") -> str:
        """
        Asynchronously exports the actuator configuration parameters to an INI file.
        This method reads a predefined set of actuator configuration parameters from the device,
        and writes them to an INI file. The file can be saved to a specified path and filename,
        or defaults will be used based on the actuator's description and serial number.

        Args:
            path (str, optional): Directory path where the configuration file will be saved.
                If not provided, the file will be saved in the current working directory.
            filename (str, optional): Name of the configuration file. If not provided,
                a default name in the format 'actuator_conf_{desc}_{acserno}.ini' will be used.

        Returns:
            The full path to the saved configuration file.

        Raises:
            Any exceptions raised during file writing or parameter reading will propagate.
        """
        export_keys = [
            "desc",
            "acserno",
            "sr",
            "setlpon",
            "setlpf",
            "kp",
            "kd",
            "ki",
            "notchf",
            "notchb",
            "notchon",
            "poslpon",
            "poslpf",
            "modsrc",
            "cl",
            "pcf",
        ]
        config_values: Dict[str, str] = {}
        for key in export_keys:
            value = await self.read_response_parameters_string(key)
            config_values[key] = value

        config_data: Dict[str, Dict[str, str]] = {}
        config_data['Actuator Configuration'] = config_values
        config = configparser.ConfigParser()
        config.read_dict(config_data)
        if not filename:
            filename = f"actuator_conf_{config_values["desc"]}_{config_values["acserno"]}.ini"

        full_path = os.path.join(path, filename) if path else filename
        with open(full_path, 'w') as configfile:
            config.write(configfile)
        return full_path


    async def import_actuator_config(self, filepath: str):
        """
        Imports actuator configuration from an INI file.

        Args:
            filepath: Path to the INI file with the actuator configuration.
        """
        import_keys = {
            "sr",
            "setlpon",
            "setlpf",
            "kp",
            "kd",
            "ki",
            "notchf",
            "notchb",
            "notchon",
            "poslpon",
            "poslpf",
            "modsrc",
            "cl",
            "pcf",
        }

        config = configparser.ConfigParser()
        config.read(filepath)

        if "Actuator Configuration" not in config:
            raise ValueError(f"'Actuator Configuration' section not found in {filepath}")

        for key, value in config["Actuator Configuration"].items():
            if key not in import_keys:
                continue
            command = f"{key},{value}"
            await self.write(command)


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

    

    async def set_control_mode(self, mode: CtrlMode) -> None:
        """
        Sets the control mode of the device.

        Args:
            mode (CtrlMode): The control mode to set.
        """
        await self.write_value("ctrlmode", mode.value)


    async def get_control_mode(self) -> CtrlMode:
        """
        Retrieves the current control mode of the device.

        Returns:
            CtrlMode: The current control mode.
        """
        return CtrlMode(await self.read_int_value('ctrlmode'))