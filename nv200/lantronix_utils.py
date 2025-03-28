from typing import List, Tuple, Dict

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