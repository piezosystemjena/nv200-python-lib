import socket
import psutil

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
