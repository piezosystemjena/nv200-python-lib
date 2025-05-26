import socket
import psutil
import ipaddress
import re


def is_valid_ip(address: str) -> bool:
    """
    Returns True if the string is a valid IPv4 or IPv6 address, False otherwise.
    """
    try:
        ipaddress.ip_address(address)
        return True
    except ValueError:
        return False


_MAC_REGEX = re.compile(
    r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$|'          # e.g. 01:23:45:67:89:ab or 01-23-45-67-89-ab
    r'^([0-9A-Fa-f]{12})$'                                  # e.g. 0123456789ab (no separators)
)


def is_valid_mac(address: str) -> bool:
    """
    Returns True if the string is a valid MAC address (common formats), False otherwise.
    """
    return bool(_MAC_REGEX.match(address))


def get_active_ethernet_ips():
    """
    Retrieve a list of active Ethernet interface names and their associated IPv4 addresses.
    This function checks the network interfaces on the system and identifies those
    that are active (UP). It then collects the IPv4 addresses associated with these
    active interfaces.
    
    Returns:
        list of tuple: A list of tuples where each tuple contains the interface name (str)
        and its corresponding IPv4 address (str).
    """
    active_ethernet_ips = []
    
    # Retrieve network statistics (contains information about the status)
    stats = psutil.net_if_stats()
    
    # Iterate through all interfaces
    for interface, addrs in psutil.net_if_addrs().items():
        # Check if the interface is active (UP)
        # if stats[interface].isup and ("eth" in interface.lower() or "en" in interface.lower()):
        if stats[interface].isup:
            for addr in addrs:
                if addr.family == socket.AF_INET:  # Only IPv4 addresses
                    active_ethernet_ips.append((interface, addr.address))
    
    return active_ethernet_ips
