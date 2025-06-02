
"""
This module defines enumerations, classes, and data structures for representing device types,
status flags, error codes, and related information for NV200 devices.

Classes and Enums:
------------------
- :class:`.PidLoopMode` (Enum): Modes of operation for a PID control loop (open/closed loop).
- :class:`.ErrorCode` (Enum): Error codes and descriptions for device errors.
- :class:`.StatusFlags` (IntFlag): Bit flags representing the status register of a device.
- :class:`.ModulationSource` (Enum): Sources for setpoint modulation.
- :class:`.StatusRegister`: Class for parsing and representing a 16-bit status register.
- :class:`.DeviceError` (Exception): Custom exception for device-related errors.
- :class:`.TransportType` (Enum): Supported transport types (telnet, serial).
- :class:`.DetectedDevice` (dataclass): Structure for detected device information.


Functionality:
--------------
- Provides enums for device modes, errors, and status flags.
- Offers utility methods for error code conversion and description lookup.
- Parses and interprets status register values.
- Defines a custom exception for device errors.
- Structures device detection information for network or serial connections.
"""    

from enum import Enum, IntFlag, Flag, auto
from dataclasses import dataclass
from typing import Optional


class PidLoopMode(Enum):
    """
    PidLoopMode is an enumeration that defines the modes of operation for a PID control loop.
    """
    OPEN_LOOP = 0
    CLOSED_LOOP = 1

class ErrorCode(Enum):
    """
    ErrorCode(Enum):
        An enumeration representing various error codes and their corresponding descriptions.
    """
    ERROR_NOT_SPECIFIED = 1
    UNKNOWN_COMMAND = 2
    PARAMETER_MISSING = 3
    ADMISSIBLE_PARAMETER_RANGE_EXCEEDED = 4
    COMMAND_PARAMETER_COUNT_EXCEEDED = 5
    PARAMETER_LOCKED_OR_READ_ONLY = 6
    UNDERLOAD = 7
    OVERLOAD = 8
    PARAMETER_TOO_LOW = 9
    PARAMETER_TOO_HIGH = 10

    @classmethod
    def from_value(cls, value : int):
        """Convert an integer into an ErrorCode enum member."""
        if value in cls._value2member_map_:
            return cls(value)
        else:
            return cls.ERROR_NOT_SPECIFIED  # Default error if value is invalid

    # Method to get the error description based on the error code
    @classmethod
    def get_description(cls, error_code) -> str:
        """
        Retrieves a human-readable description for a given error code.

        Args:
            error_code (int): The error code for which the description is requested.

        Returns:
            str: A string describing the error associated with the provided error code.
                 If the error code is not recognized, "Unknown error" is returned.
        """
        descriptions = {
            cls.ERROR_NOT_SPECIFIED: "Error not specified",
            cls.UNKNOWN_COMMAND: "Unknown command",
            cls.PARAMETER_MISSING: "Parameter missing",
            cls.ADMISSIBLE_PARAMETER_RANGE_EXCEEDED: "Admissible parameter range exceeded",
            cls.COMMAND_PARAMETER_COUNT_EXCEEDED: "Command's parameter count exceeded",
            cls.PARAMETER_LOCKED_OR_READ_ONLY: "Parameter is locked or read only",
            cls.UNDERLOAD: "Underload",
            cls.OVERLOAD: "Overload",
            cls.PARAMETER_TOO_LOW: "Parameter too low",
            cls.PARAMETER_TOO_HIGH: "Parameter too high"
        }
        return descriptions.get(error_code, "Unknown error")
    
class StatusFlags(IntFlag):
    """
    Enum representing the individual status flags within a 16-bit status register.
    """
    ACTUATOR_CONNECTED = 1 << 0
    SENSOR_TYPE_0 = 1 << 1
    SENSOR_TYPE_1 = 1 << 2
    CLOSED_LOOP_MODE = 1 << 3
    LOW_PASS_FILTER_ON = 1 << 4
    NOTCH_FILTER_ON = 1 << 5
    SIGNAL_PROCESSING_ACTIVE = 1 << 7
    AMPLIFIER_CHANNELS_BRIDGED = 1 << 8
    TEMPERATURE_TOO_HIGH = 1 << 10
    ACTUATOR_ERROR = 1 << 11
    HARDWARE_ERROR = 1 << 12
    I2C_ERROR = 1 << 13
    LOWER_CONTROL_LIMIT_REACHED = 1 << 14
    UPPER_CONTROL_LIMIT_REACHED = 1 << 15

    @staticmethod
    def get_sensor_type(value):
        """
        Determines the type of sensor based on the sensor bits in the status register.
        
        :param value: The 16-bit status register value.
        :return: A string describing the sensor type.
        """
        sensor_bits = (value & (StatusFlags.SENSOR_TYPE_0 | StatusFlags.SENSOR_TYPE_1)) >> 1
        sensor_types = {
            0b00: "No position sensor",
            0b01: "Strain gauge sensor",
            0b10: "Capacitive sensor"
        }
        return sensor_types.get(sensor_bits, "Unknown")
    

class ModulationSource(Enum):
    """
    Enumeration for setpoint modulation source.
    """
    USB_ETHERNET = 0
    ANALOG_IN = 1
    SPI = 2
    WAVEFORM_GENERATOR = 3


class StatusRegister:
    """
    A class representing the 16-bit status register of an actuator or amplifier.
    """
    def __init__(self, value: int):
        """
        Initializes the StatusRegister with a given 16-bit value.
        
        :param value: The 16-bit status register value.
        """
        self.flags = StatusFlags(value)
        self.value = value

    def has_flag(self, flag: StatusFlags):
        """
        Checks if a given status flag is set in the register.
        
        :param flag: A StatusFlags enum value to check.
        :return: True if the flag is set, False otherwise.
        """
        return bool(self.flags & flag)

    def __repr__(self):
        """
        Provides a string representation of the status register with human-readable information.
        
        :return: A formatted string showing the status register details.
        """
        return (f"StatusRegister(value={self.value:#06x}):\n"
                f"\tActuator Connected={self.has_flag(StatusFlags.ACTUATOR_CONNECTED)}\n"
                f"\tSensor={StatusFlags.get_sensor_type(self.value)}\n"
                f"\tClosed Loop Mode={self.has_flag(StatusFlags.CLOSED_LOOP_MODE)}\n"
                f"\tLow Pass Filter={self.has_flag(StatusFlags.LOW_PASS_FILTER_ON)}\n"
                f"\tNotch Filter={self.has_flag(StatusFlags.NOTCH_FILTER_ON)}\n"
                f"\tSignal Processing={self.has_flag(StatusFlags.SIGNAL_PROCESSING_ACTIVE)}\n"
                f"\tBridged Amplifier={self.has_flag(StatusFlags.AMPLIFIER_CHANNELS_BRIDGED)}\n"
                f"\tTemp High={self.has_flag(StatusFlags.TEMPERATURE_TOO_HIGH)}\n"
                f"\tActuator Error={self.has_flag(StatusFlags.ACTUATOR_ERROR)}\n"
                f"\tHardware Error={self.has_flag(StatusFlags.HARDWARE_ERROR)}\n"
                f"\tI2C Error={self.has_flag(StatusFlags.I2C_ERROR)}\n"
                f"\tLower Limit Reached={self.has_flag(StatusFlags.LOWER_CONTROL_LIMIT_REACHED)}\n"
                f"\tUpper Limit Reached={self.has_flag(StatusFlags.UPPER_CONTROL_LIMIT_REACHED)}")


class DeviceError(Exception):
    """
    Custom exception class for handling device-related errors.

    Attributes:
        error_code (ErrorCode): The error code associated with the exception.
        description (str): A human-readable description of the error.

    Args:
        error_code (ErrorCode): An instance of the ErrorCode enum representing the error.

    Raises:
        ValueError: If the provided error_code is not a valid instance of the ErrorCode enum.
    """
    def __init__(self, error_code : ErrorCode):
        self.error_code = error_code
        self.description = ErrorCode.get_description(error_code)
        # Call the base class constructor with the formatted error message
        super().__init__(f"Error {self.error_code.value}: {self.description}")


class TransportType(str, Enum):
    """
    Enumeration of supported transport types for device communication.

    Attributes:
        TELNET: Represents the Telnet protocol for network communication.
        SERIAL: Represents serial communication (e.g., RS-232).
    """
    TELNET = "telnet"
    SERIAL = "serial"

    def __str__(self):
        """
        Returns a string representation of the transport type, capitalized.
        """
        return self.name.capitalize()
    
@dataclass
class TransportProtocolInfo:
    """
    Represents the protocol information for a transport type.
    """
    transport: TransportType
    identifier: str  # e.g., IP or serial port
    mac: Optional[str] = None   

    def __str__(self):
        """
        Returns a string representation of the TransportProtocolInfo.
        """
        return f"{self.transport} @ {self.identifier}"
    

@dataclass
class DeviceInfo:
    """
    Represents information about a device, including its transport type, identifier, and optional metadata.

    Attributes:
        transport (TransportType): The type of transport used to communicate with the device.
        identifier (str): The primary identifier for the device (e.g., IP address or serial port).
        mac (Optional[str]): The MAC address of the device, if available.
        device_id (Optional[str]): A unique identifier for the device, if available.
    """
    transport_info: TransportProtocolInfo
    device_id: Optional[str] = None  # Unique identifier for the device, if available

    def __str__(self):
        """
        Returns a string representation of the transport type, capitalized.
        """
        device_info = f"{self.transport_info}"
        if self.device_id:
            device_info += f" - {self.device_id}"
        return device_info


@dataclass
class DetectedDevice:
    """
    Represents a device detected on the network or via serial connection

    Attributes:
        transport (TransportType): The transport type used to communicate with the device (e.g., Ethernet, Serial).
        identifier (str): A unique identifier for the device, such as an IP address or serial port name.
        mac (Optional[str]): The MAC address of the device, if available.
        device_id (Optional[str]): A unique identifier for the device, if available. such as NV200/D_NET
        actuator_name (Optional[str]): The name of the connected piezo actuator, if available - e.g., "TRITOR100SG".
        actuator_serial (Optional[str]): The serial number of the connected piezo actuator, if available.
    """
    transport: TransportType
    identifier: str  # e.g., IP or serial port
    mac: Optional[str] = None
    device_id: Optional[str] = None  # Unique identifier for the device, if available
    actuator_name: Optional[str] = None
    actuator_serial: Optional[str] = None
    
    def __str__(self):
        """
        Returns a string representation of the transport type, capitalized.
        """
        device_info = f"{self.transport} @ {self.identifier}"
        if self.mac:
            device_info += f" (MAC: {self.mac})"

        if self.device_id:
            device_info += f" - {self.device_id}"
        return f"{device_info} - Actuator: {self.actuator_name} #{self.actuator_serial}"

    

class DiscoverFlags(Flag):
    """
    Flags to configure the behavior of the device discovery process.

    These flags can be combined using the bitwise OR (`|`) operator.

    Attributes:
        DETECT_SERIAL: Enables detection of serial devices.
        DETECT_ETHERNET: Enables detection of ethernet devices.
        READ_DEVICE_INF: Enriches discovered devices with additional information such as actuator name and actuator serial number.
        ALL: Enables all discovery actions (serial, ethernet, and enrichment).
    """
    DETECT_SERIAL = auto()
    DETECT_ETHERNET = auto()
    READ_DEVICE_INFO = auto()
    ALL_INTERFACES = DETECT_SERIAL | DETECT_ETHERNET
    ALL = ALL_INTERFACES | READ_DEVICE_INFO
    

    @staticmethod
    def flags_for_transport(transport: Optional[TransportType] = None) -> 'DiscoverFlags':
        """
        Maps a TransportType to the appropriate DiscoverFlags.

        Args:
            transport: The transport type (e.g., SERIAL or TELNET)

        Returns:
            DiscoverFlags corresponding to the selected transport type.
        """
        if transport is None:
            return DiscoverFlags.ALL_INTERFACES
        elif transport == TransportType.SERIAL:
            return DiscoverFlags.DETECT_SERIAL
        elif transport == TransportType.TELNET:
            return DiscoverFlags.DETECT_ETHERNET
        else:
            raise ValueError(f"Unsupported transport type: {transport}")


@dataclass
class NetworkEndpoint:
    """
    Represents a network endpoint identified by a MAC and IP address.

    Attributes:
        mac (str): The MAC (Media Access Control) address of the endpoint,
                   typically in the format '00:1A:2B:3C:4D:5E'.
        ip (str): The IPv4 or IPv6 address of the endpoint,
                  e.g., '192.168.1.100'
    """
    mac: str
    ip: str

    def __str__(self) -> str:
        """Returns a user-friendly string representation of the endpoint."""
        return f"MAC={self.mac}, IP={self.ip}"
