import socket
from typing import List, Tuple, Dict, Optional
from nv200.eth_utils import get_active_ethernet_ips
from nv200.lantronix_utils import parse_responses


# Define constants
BROADCAST_IP = '255.255.255.255'
UDP_PORT = 30718  # Lantronix Discovery Protocol port
TELNET_PORT = 23  # Telnet Port (default: 23)
TIMEOUT = 0.4  # Timeout for UDP response


def send_udp_broadcast(local_ip : str) -> List[Tuple[bytes, Tuple[str, int]]]:
    """
    Sends a UDP broadcast to discover devices on the network. It sends a broadcast message
    and listens for responses within a specified timeout period.

    Returns:
        List[Tuple[bytes, Tuple[str, int]]]:
            A list of tuples where each tuple contains:
            - The received raw data (bytes) from the device.
            - The sender's address, which is a tuple of IP (str) and port (int).
            An empty list is returned if no responses are received or if an error occurs.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((local_ip, UDP_PORT))
    s.settimeout(TIMEOUT)

    try:
        # Send discovery packet (Lantronix Device Discovery Protocol)
        s.sendto(bytearray([0x00, 0x00, 0x00, 0xF6]), (BROADCAST_IP, UDP_PORT))

        broadcast_responses = []
        while True:
            try:
                received_data = s.recvfrom(65565)  # Receive message (msg, (ip, port))
                broadcast_responses.append(received_data)
            except socket.timeout:
                break  # Exit loop when no more responses arrive

    except (ValueError, IndexError) as e:
        print(f"Error sending UDP broadcast: {e}")
        broadcast_responses = []

    finally:
        s.close()  # Ensure socket is closed
    return broadcast_responses


def find_device_by_mac(device_list: List[Dict[str, str]], target_mac: str) -> Optional[str]:
    """
    Searches for a device by its MAC address in the list of discovered devices.

    Args:
        devices (List[Dict[str, str]]):
            A list of dictionaries, each containing the 'MAC' and 'IP' of a device.
        target_mac (str):
            The MAC address to search for.

    Returns:
        Optional[str]:
            The IP address of the device if found, or None if the device is not found.
    """
    for dev in device_list:
        if dev['MAC'] == target_mac:
            return dev['IP']
    return None


def discover_lantronix_devices() -> List[Dict[str, str]]:
    """
    Discovers Lantronix devices on the network by sending UDP broadcast messages
    from all active Ethernet interfaces and parsing their responses.

    Returns:
        List[Dict[str, str]]:
            A list of dictionaries where each dictionary contains:
            - 'MAC' (str): The MAC address of the responding device.
            - 'IP' (str): The IP address of the responding device.
    """
    for _, ip in get_active_ethernet_ips():
        device_responses = send_udp_broadcast(ip)
        if not device_responses:
            continue
        device_list = parse_responses(device_responses)
        if device_list:
            return device_list
    return []


def discover_lantronix_device(target_mac: str) -> Optional[str]:
    """
    Discover a specific Lantronix device on the network by its MAC address.

    This function scans the network for Lantronix devices and attempts to find
    the device that matches the provided MAC address.

    Args:
            target_mac (str): The MAC address of the target Lantronix device.

    Returns:
           Optional[str]:
               The IP address of the device if found, or None if the device is not found.

    Raises:
            ValueError: If the provided MAC address is invalid.
    """
    devices = discover_lantronix_devices()
    return find_device_by_mac(devices, target_mac)


# Main Execution
if __name__ == "__main__":
    # Desired MAC address of NV200D/NET
    TARGET_MAC: str = "00:80:A3:79:C6:18"
    ip = discover_lantronix_device(TARGET_MAC)
    if ip:
        print(f"Device with MAC {TARGET_MAC} found at IP: {ip}")
    else:
        print(f"Device with MAC {TARGET_MAC} not found.")
