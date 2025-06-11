"""
This module provides asynchronous device discovery functionality for the NV200 library.
It concurrently scans for devices available via Telnet and Serial protocols, returning
a unified list of detected devices. Each detected device is represented by a :class:`.DetectedDevice`
instance, annotated with its transport type (TELNET or SERIAL), identifier (such as IP address
or serial port), and optionally a MAC address.
"""

import asyncio
import logging
from typing import List, Type, Optional
from nv200.device_factory import create_device_from_id
from nv200.transport_protocol import TransportProtocol
from nv200.telnet_protocol import TelnetProtocol  
from nv200.serial_protocol import SerialProtocol
from nv200.shared_types import DetectedDevice, TransportType, DiscoverFlags
from nv200.device_base import PiezoDeviceBase
from nv200.transport_factory import transport_from_detected_device


# Global module locker
logger = logging.getLogger(__name__)



async def _enrich_device_info(detected_device: DetectedDevice, flags: DiscoverFlags) -> DetectedDevice:
    """
    Asynchronously enriches a DetectedDevice object with additional actuator information.

    Returns:
        DetectedDevice: The enriched device information object with actuator name and serial number populated.
    """
    try:
        logger.debug("Reading device ID from: %s", detected_device.identifier)
        protocol = transport_from_detected_device(detected_device)
        await protocol.connect(auto_adjust_comm_params=bool(flags & DiscoverFlags.ADJUST_COMM_PARAMS))
        dev = PiezoDeviceBase(protocol)
        detected_device.device_id = await dev.get_device_type()
        logger.debug("Device ID detected: %s", detected_device.device_id)
        dev = create_device_from_id(detected_device.device_id, protocol)
        await dev.enrich_device_info(detected_device)
        await protocol.close()
        return detected_device
    except Exception:
        return None
      

async def discover_devices(flags: DiscoverFlags = DiscoverFlags.ALL_INTERFACES, device_class: Optional[Type[PiezoDeviceBase]] = None) -> List[DetectedDevice]:
    """
    Asynchronously discovers devices on available interfaces based on the specified discovery flags and optional device class.

    The discovery process can be customized using flags to enable or disable:

    - `DiscoverFlags.DETECT_ETHERNET` - detect devices connected via Ethernet
    - `DiscoverFlags.DETECT_SERIAL` - detect devices connected via Serial
    - `DiscoverFlags.READ_DEVICE_INFO` - enrich device information with additional details such as actuator name and actuator serial number    

    Args:
        flags (DiscoverFlags, optional): Flags indicating which interfaces to scan and whether to read device info. Defaults to DiscoverFlags.ALL_INTERFACES.
        device_class (Optional[Type[PiezoDeviceBase]], optional): If specified, only devices matching this class will be returned. Also ensures device info is read.

    Returns:
        List[DetectedDevice]: A list of detected devices, optionally enriched with detailed information and filtered by device class.

    Raises:
        Any exceptions raised by underlying protocol discovery or enrichment functions.

    Notes:
        - Device discovery is performed in parallel for supported interfaces (Ethernet, Serial).
        - If READ_DEVICE_INFO is set, each detected device is enriched with additional information.
        - If device_class is specified, only devices matching the class's DEVICE_ID are returned.

    Examples:
        Discover all Devices on all interfaces

        >>> device = await nv200.device_discovery.discover_devices(DiscoverFlags.ALL_INTERFACES | DiscoverFlags.READ_DEVICE_INFO)

        Discover NV200 Devices connected via serial interface

        >>> device = await nv200.device_discovery.discover_devices(DiscoverFlags.DETECT_SERIAL | DiscoverFlags.READ_DEVICE_INFO, NV200Device)
    """

    devices: List[DetectedDevice] = []
    tasks = []

    if device_class:
        flags |= DiscoverFlags.READ_DEVICE_INFO  # Ensure we read device info if a specific class is requested

    if flags & DiscoverFlags.DETECT_ETHERNET:
        tasks.append(TelnetProtocol.discover_devices(flags))
    else:
        tasks.append(asyncio.sleep(0, result=[]))  # Placeholder for parallel await

    if flags & DiscoverFlags.DETECT_SERIAL:
        tasks.append(SerialProtocol.discover_devices(flags))
    else:
        tasks.append(asyncio.sleep(0, result=[]))  # Placeholder for parallel await

    eth_devs, serial_devs = await asyncio.gather(*tasks)

    if flags & DiscoverFlags.DETECT_ETHERNET:
        devices.extend(eth_devs)

    if flags & DiscoverFlags.DETECT_SERIAL:
        devices.extend(serial_devs)

    if flags & DiscoverFlags.READ_DEVICE_INFO:
        # Enrich each device with detailed info
        logger.debug("Enriching %d devices with detailed info...", len(devices))
        raw_results = await asyncio.gather(*(_enrich_device_info(d, flags) for d in devices))
        devices = [d for d in raw_results if d is not None]

    if device_class:
        # Filter devices by the specified device class
        devices = [d for d in devices if d.device_id == device_class.DEVICE_ID]

    return devices
