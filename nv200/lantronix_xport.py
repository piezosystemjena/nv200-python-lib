import asyncio
import socket
from typing import List, Tuple, Dict, Optional
from nv200.eth_utils import get_active_ethernet_ips

# Define constants
BROADCAST_IP = '255.255.255.255'
UDP_PORT = 30718  # Lantronix Discovery Protocol port
TELNET_PORT = 23  # Telnet Port (default: 23)
TIMEOUT = 0.4  # Timeout for UDP response


async def send_udp_broadcast_async(local_ip : str) -> List[Tuple[bytes, Tuple[str, int]]]:
    """
    Asynchronously sends a UDP broadcast to discover devices on the network. It sends a broadcast message
    and listens for responses within a specified timeout period.

    Returns:
        List[Tuple[bytes, Tuple[str, int]]]:
            A list of tuples where each tuple contains:
            - The received raw data (bytes) from the device.
            - The sender's address, which is a tuple of IP (str) and port (int).
            An empty list is returned if no responses are received or if an error occurs.
    """
    # Create a UDP socket
    loop = asyncio.get_event_loop()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((local_ip, UDP_PORT))
    s.setblocking(False)  # Non-blocking mode

    # List to store responses
    broadcast_responses = []

    # Set up a UDP broadcast message
    try:
        s.sendto(bytearray([0x00, 0x00, 0x00, 0xF6]), (BROADCAST_IP, UDP_PORT))  # Lantronix Discovery Packet

        # Timeout for receiving responses
        async def receive_response():
            while True:
                received_data = await loop.sock_recvfrom(s, 65565)
                broadcast_responses.append(received_data)

        # Use asyncio's event loop to wait for responses
        await asyncio.wait_for(receive_response(), timeout=TIMEOUT)
    except asyncio.TimeoutError:
        pass
    except (ValueError, IndexError) as e:
        print(f"Error sending UDP broadcast: {e}")
        broadcast_responses = []
    finally:
        s.close()

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


async def discover_lantronix_devices_async() -> List[Dict[str, str]]:
    """
    Discovers Lantronix devices on the network by sending UDP broadcast messages
    from all active Ethernet interfaces and parsing their responses.

    Returns:
        List[Dict[str, str]]:
            A list of dictionaries where each dictionary contains:
            - 'MAC' (str): The MAC address of the responding device.
            - 'IP' (str): The IP address of the responding device.
    """
    device_list: List[Dict[str, str]] = []
    ips = [ip for _, ip in get_active_ethernet_ips()]

    async def discover_from_ip(ip: str) -> List[Dict[str, str]]:
        responses = await send_udp_broadcast_async(ip)
        return parse_responses(responses) if responses else []

    # Launch all discovery coroutines in parallel
    results = await asyncio.gather(*(discover_from_ip(ip) for ip in ips))

    # Flatten list of lists
    for r in results:
        device_list.extend(r)

    return device_list


async def discover_lantronix_device_async(target_mac: str) -> Optional[str]:
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
    devices = await discover_lantronix_devices_async()
    return find_device_by_mac(devices, target_mac)


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


LANTRONIX_RESPONSE_SIZE = 30  # Expected size of Lantronix response
LAMNTONIX_MAC_PREFIX = "00:80:A3"  # Lantronix MAC address prefix

def parse_responses(response_list: List[Tuple[bytes, Tuple[str, int]]]) -> List[Dict[str, str]]:
    """
    Parses the received responses from the devices to extract their MAC and IP addresses.

    Args:
        responses (List[Tuple[bytes, Tuple[str, int]]]):
            A list of tuples, each containing:
            - The raw data (bytes) received from the device.
            - The sender's address, which is a tuple containing IP (str) and port (int).

    Returns:
        List[Dict[str, str]]:
            A list of dictionaries where each dictionary contains:
            - 'MAC' (str): The MAC address of the responding device.
            - 'IP' (str): The IP address of the responding device.
    """
    parsed_devices = []
    for data, address in response_list:
        try:
            if len(data) != LANTRONIX_RESPONSE_SIZE:
                continue
            mac_hex = data.hex()
            mac_address = ':'.join(mac_hex[48:60][i:i + 2] for i in range(0, 12, 2)).upper()
            if not mac_address.startswith(LAMNTONIX_MAC_PREFIX):
                continue
            parsed_devices.append({'MAC': mac_address, 'IP': address[0]})
        except Exception as e:
            print(f"Error parsing response: {e}")

    return parsed_devices



# async Main execution
async def main_async():
    TARGET_MAC: str = "00:80:A3:79:C6:18"
    ip = await discover_lantronix_device_async(TARGET_MAC)
    if ip:
        print(f"Device with MAC {TARGET_MAC} found at IP: {ip}")
    else:
        print(f"Device with MAC {TARGET_MAC} not found.")

def main():
    TARGET_MAC: str = "00:80:A3:79:C6:18"
    ip = discover_lantronix_device(TARGET_MAC)
    if ip:
        print(f"Device with MAC {TARGET_MAC} found at IP: {ip}")
    else:
        print(f"Device with MAC {TARGET_MAC} not found.")


# Running the async main function
if __name__ == "__main__":
    asyncio.run(main_async())
    main()

