import logging
from typing import Type
from nv200.nv200_device import NV200Device
from nv200.shared_types import DetectedDevice, TransportType, DiscoverFlags
from nv200.device_discovery import discover_devices
from nv200.transport_protocol import TransportProtocol
from nv200.telnet_protocol import TelnetProtocol
from nv200.serial_protocol import SerialProtocol
from nv200.eth_utils import is_valid_ip, is_valid_mac
from nv200.device_base import PiezoDeviceBase
from typing import List, Optional
import nv200.lantronix_xport as xport


# Global module locker
logger = logging.getLogger(__name__)

async def connect_to_single_device(device_class: Type[PiezoDeviceBase], transport_type : Optional[TransportType] = None, interface_or_address : str = None) -> PiezoDeviceBase:
    """
    Convenience function to quickly connect to a single device.

    Use this function if you only have one single device connected and you would like to connect to
    it directly. If no transport type is specified, it will attempt to connect using the serial transport first,
    and if no devices are found, it will then attempt to connect using the Telnet transport.
    The function does not verify if the right device is connected, it simply connects to the first device found.
    So use this function only, if you really have only one device connected to your system.

    If no transport type is specified, the function will perform auto discovery of devices. If transport type is specified,
    but no interface_or_address is provided, it will perform auto discovery of devices for that transport type.
    If both transport type and interface_or_address are specified, it will attempt to connect directly to the specified device.

    Args:
        transport_type (TransportType, optional): The type of transport to use (e.g., Serial, Telnet).
            If not specified, it will attempt to connect using serial transport first, then Telnet.

        interface_or_address (str, optional): The serial port, IP address, or MAC address to connect to.
                If not specified, device discovery is performed. This parameter is only used if the 
                transport type is specified. If no transport type is specified, it will attempt to discover devices
                automatically.

    Returns:
        DeviceClient: An instance of DeviceClient connected to the NV200 device.

    Examples:
        Auto Discovery

        >>> device = await nv200.connection_utils.connect_to_single_device()

        Serial Port Auto Discovery

        >>> device = await nv200.connection_utils.connect_to_single_device(TransportType.SERIAL)

        Ethernet Auto Discovery
        
        >>> device = await nv200.connection_utils.connect_to_single_device(TransportType.TELNET)

        Connect to specific MAC address

        >>> device = await nv200.connection_utils.connect_to_single_device(TransportType.TELNET, "00:80:A3:79:C6:18")

        Connect to specific IP address

        >>> device = await nv200.connection_utils.connect_to_single_device(TransportType.TELNET, "192.168.102.3")

        Connect to specific serial port

        >>> device = await nv200.connection_utils.connect_to_single_device(TransportType.SERIAL, "COM3")
    """
    dev : PiezoDeviceBase = None
    transport: TransportProtocol = None
    if transport_type is TransportType.SERIAL and interface_or_address:
        transport = SerialProtocol(port=interface_or_address)
    elif transport_type is TransportType.TELNET and interface_or_address:
        if is_valid_ip(interface_or_address):
            transport = TelnetProtocol(host=interface_or_address)
        elif is_valid_mac(interface_or_address):
            transport = TelnetProtocol(MAC=interface_or_address)
        else:
            raise ValueError("Invalid IP address or MAC address provided for Telnet transport.")

    if transport:
        dev = device_class(transport=transport)
        await dev.connect(auto_adjust_comm_params=False)
        return dev

    logger.info("No transport type and address specified, attempting to discover devices...")
    detected_devices: List[DetectedDevice] = []
    discover_flags = DiscoverFlags.flags_for_transport(transport_type)
    if discover_flags & DiscoverFlags.DETECT_SERIAL:
        detected_devices = await discover_devices(DiscoverFlags.flags_for_transport(TransportType.SERIAL))

    if not detected_devices and discover_flags & DiscoverFlags.DETECT_ETHERNET:
        network_endpoints = await xport.discover_lantronix_devices_async()
        for network_endpoint in network_endpoints:
            detected_devices.append(DetectedDevice(
                    transport=TransportType.TELNET,
                    identifier=network_endpoint.ip,
                    mac=network_endpoint.mac
                ))
    
    if not detected_devices:
        raise RuntimeError("No devices found during discovery.")
    device = NV200Device.from_detected_device(detected_devices[0])
    await device.connect(auto_adjust_comm_params=False)

    return device
