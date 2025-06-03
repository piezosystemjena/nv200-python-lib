"""
This module provides asynchronous device discovery functionality for the NV200 library.
It concurrently scans for devices available via Telnet and Serial protocols, returning
a unified list of detected devices. Each detected device is represented by a :class:`.DetectedDevice`
instance, annotated with its transport type (TELNET or SERIAL), identifier (such as IP address
or serial port), and optionally a MAC address.
"""

import asyncio
import logging
from typing import List
from nv200.transport_protocol import TransportProtocol
from nv200.telnet_protocol import TelnetProtocol  
from nv200.serial_protocol import SerialProtocol
from nv200.shared_types import DetectedDevice, TransportType, DiscoverFlags
from nv200.device_base import PiezoDeviceBase, create_device_from_id


# Global module locker
logger = logging.getLogger(__name__)


def _transport_from_detected_device(detected_device: DetectedDevice) -> "TransportProtocol":
    """
    Creates and returns a transport protocol instance based on the detected device's transport type.
    """
    if detected_device.transport == TransportType.TELNET:
        return TelnetProtocol(host = detected_device.identifier)
    elif detected_device.transport == TransportType.SERIAL:
        return SerialProtocol(port = detected_device.identifier)
    else:
        raise ValueError(f"Unsupported transport type: {detected_device.transport}")
    

async def _enrich_device_info(detected_device: DetectedDevice) -> None:
    """
    Asynchronously enriches a DetectedDevice object with additional actuator information.

    Returns:
        DetectedDevice: The enriched device information object with actuator name and serial number populated.
    """
    try:
        logger.debug("Reading device ID from: %s", detected_device.identifier)
        protocol = _transport_from_detected_device(detected_device)
        await protocol.connect(auto_adjust_comm_params=False)
        dev = PiezoDeviceBase(protocol)
        detected_device.device_id = await dev.get_device_type()
        logger.debug("Device ID detected: %s", detected_device.device_id)
        dev = create_device_from_id(detected_device.device_id, protocol)
        await dev.enrich_device_info(detected_device)
        return detected_device
    except Exception:
        return None
    

async def discover_devices(flags: DiscoverFlags = DiscoverFlags.ALL_INTERFACES) -> List[DetectedDevice]:
    """
    Asynchronously discovers available devices over Telnet and Serial protocols, with optional enrichment.
    The discovery process can be customized using flags to enable or disable:

      - `DiscoverFlags.DETECT_ETHERNET` - detect devices connected via Ethernet
      - `DiscoverFlags.DETECT_SERIAL` - detect devices connected via Serial
      - `DiscoverFlags.READ_DEVICE_INFO` - enrich device information with additional details such as actuator name and actuator serial number

    Args:
        flags (DiscoverFlags): Bitwise combination of discovery options. Defaults to ALL_INTERFACES.

    Returns:
        List[DetectedDevice]: A list of detected and optionally enriched devices.

    Note:
        The flag EXTENDED_INFO may involve additional communication with each device and takes more time.
    """
    devices: List[DetectedDevice] = []
    tasks = []

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
        raw_results = await asyncio.gather(*(_enrich_device_info(d) for d in devices))
        devices = [d for d in raw_results if d is not None]

    return devices
