"""
This module provides asynchronous device discovery functionality for the NV200 library.
It concurrently scans for devices available via Telnet and Serial protocols, returning
a unified list of detected devices. Each detected device is represented by a :class:`.DetectedDevice`
instance, annotated with its transport type (TELNET or SERIAL), identifier (such as IP address
or serial port), and optionally a MAC address.
"""

import asyncio
import logging
from typing import List, Optional, Callable, Awaitable
from nv200.transport_protocol import TransportProtocol
from nv200.telnet_protocol import TelnetProtocol  
from nv200.serial_protocol import SerialProtocol
from nv200.shared_types import DetectedDevice, TransportType, DiscoverFlags, NetworkEndpoint
from nv200.nv200_device import NV200Device


# Global module locker
logger = logging.getLogger(__name__)



async def _enrich_device_info(dev_info: DetectedDevice) -> Optional[DetectedDevice]:
    """
    Asynchronously enriches a DetectedDevice object with additional actuator information.

    Returns:
        DetectedDevice: The enriched device information object with actuator name and serial number populated.
    """
    try:
        logger.debug("Enriching device info for %s...", dev_info.identifier)
        dev = NV200Device.from_detected_device(dev_info)
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
    

async def _example_callback(proto: TransportProtocol, device: DetectedDevice) -> None:
    print("Example callback called")


async def discover_devices(flags: DiscoverFlags = DiscoverFlags.ALL_INTERFACES) -> List[DetectedDevice]:
    """
    Asynchronously discovers available devices over Telnet and Serial protocols, with optional enrichment.
    The discovery process can be customized using flags to enable or disable:

      - `DiscoverFlags.DETECT_ETHERNET` - detect devices connected via Ethernet
      - `DiscoverFlags.DETECT_SERIAL` - detect devices connected via Serial
      - `DiscoverFlags.EXTENDED_INFO` - enrich device information with additional details such as actuator name and actuator serial number

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

    eth_devs, serial_ports = await asyncio.gather(*tasks)

    if flags & DiscoverFlags.DETECT_ETHERNET:
        devices.extend(eth_devs)

    if flags & DiscoverFlags.DETECT_SERIAL:
        for port in serial_ports:
            devices.append(DetectedDevice(
                transport=TransportType.SERIAL,
                identifier=port
            ))

    if flags & DiscoverFlags.EXTENDED_INFO:
        # Enrich each device with detailed info
        logger.debug("Enriching %d devices with detailed info...", len(devices))
        raw_results = await asyncio.gather(*(_enrich_device_info(d) for d in devices))
        devices = [d for d in raw_results if d is not None]

    return devices
