"""
This module provides asynchronous device discovery functionality for the NV200 library.
It concurrently scans for devices available via Telnet and Serial protocols, returning
a unified list of detected devices. Each detected device is represented by a :class:`.DetectedDevice`
instance, annotated with its transport type (TELNET or SERIAL), identifier (such as IP address
or serial port), and optionally a MAC address.
"""

import asyncio
from typing import List
from nv200.transport_protocols import TelnetProtocol, SerialProtocol
from nv200.device_types import DetectedDevice, TransportType



async def discover_devices() -> List[DetectedDevice]:
    """
    Asynchronously discovers devices available via Telnet and Serial protocols.
    Runs Telnet and Serial device discovery concurrently, collects the results,
    and returns a combined list of DetectedDevice instances representing all found devices.
    Returns:
        List[DetectedDevice]: A list of detected devices, each annotated with its transport type
        (TELNET or SERIAL), identifier (IP address or serial port), and optionally MAC address.
    Raises:
        Any exceptions raised by the underlying TelnetProtocol or SerialProtocol discovery methods.
    """
    # Run both discovery coroutines concurrently
    telnet_task = TelnetProtocol.discover_devices()
    serial_task = SerialProtocol.discover_devices()
    
    telnet_devices, serial_ports = await asyncio.gather(telnet_task, serial_task)

    devices: List[DetectedDevice] = []

    for dev in telnet_devices:
        devices.append(DetectedDevice(
            transport=TransportType.TELNET,
            identifier=dev["IP"],
            mac=dev.get("MAC")
        ))

    for port in serial_ports:
        devices.append(DetectedDevice(
            transport=TransportType.SERIAL,
            identifier=port
        ))

    return devices
