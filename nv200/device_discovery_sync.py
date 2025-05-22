"""
Auto-generated sync wrapper for `device_discovery`.

This module provides synchronous wrappers for async functions and classes.
"""

import device_discovery
from syncwrap import run as _run

device_discovery = device_discovery

def discover_devices(full_info):
    """
    Discovers available devices over Telnet and Serial protocols.
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
    return _run(device_discovery.discover_devices(full_info))
