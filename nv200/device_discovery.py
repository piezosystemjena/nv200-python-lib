"""
This module provides asynchronous device discovery functionality for the NV200 library.
It concurrently scans for devices available via Telnet and Serial protocols, returning
a unified list of detected devices. Each detected device is represented by a :class:`.DetectedDevice`
instance, annotated with its transport type (TELNET or SERIAL), identifier (such as IP address
or serial port), and optionally a MAC address.
"""

import asyncio
import logging
from typing import List, Optional
from nv200.transport_protocols import TelnetProtocol, SerialProtocol
from nv200.device_types import DetectedDevice, TransportType
from nv200.device_interface import create_device_client


# Global module locker
logger = logging.getLogger(__name__)


async def enrich_device_info(dev_info: DetectedDevice) -> Optional[DetectedDevice]:
    """
    Asynchronously enriches a DetectedDevice object with additional actuator information.

    Returns:
        DetectedDevice: The enriched device information object with actuator name and serial number populated.
    """
    try:
        logger.debug("Enriching device info for %s...", dev_info.identifier)
        dev = create_device_client(dev_info)
        await dev.connect(auto_adjust_comm_params=False)
        dev_type = await dev.get_device_type()
        logger.debug("Device type for %s is %s", dev_info.identifier, dev_type)
        if not dev_type.startswith("NV200/D_NET"):
            logger.debug("Device type %s is not supported.", dev_type)
            await dev.close()
            return None
        dev_info.actuator_name = await dev.get_actuator_name()
        dev_info.actuator_serial = await dev.get_actuator_serial_number()
        await dev.close()
        logger.debug("Enriching device info for %s finished", dev_info.identifier)
        return dev_info
    except Exception as e:
        logger.debug("Error enriching device info for %s: %s", dev_info.identifier, e)
        await dev.close()
        return None


async def discover_devices(full_info: bool = False) -> List[DetectedDevice]:
    """
    Asynchronously discovers available devices over Telnet and Serial protocols.
    This function concurrently scans for devices using both Telnet and Serial discovery methods.
    It returns a list of DetectedDevice objects, each representing a found device. If `full_info`
    is set to True, the function will further enrich each detected device with additional
    detailed information and will discard any devices that are not of type NV200/D_NET.
    Args:
        full_info (bool, optional): If True, enriches each detected device with detailed info.
            Defaults to False.
    Returns:
        List[DetectedDevice]: A list of detected and optionally enriched device objects.
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

    if full_info:
        # Enrich each device with detailed info
        logger.debug("Enriching %d devices with detailed info...", len(devices))
        raw_results = await asyncio.gather(*(enrich_device_info(d) for d in devices))
        devices = [d for d in raw_results if d is not None]

    return devices
