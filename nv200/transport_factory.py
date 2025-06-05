from nv200.transport_protocol import TransportProtocol
from nv200.telnet_protocol import TelnetProtocol
from nv200.serial_protocol import SerialProtocol
from nv200.shared_types import DetectedDevice, TransportType



def transport_from_detected_device(detected_device: DetectedDevice) -> "TransportProtocol":
    """
    Creates and returns a transport protocol instance based on the detected device's transport type.
    """
    if detected_device.transport == TransportType.TELNET:
        return TelnetProtocol(host = detected_device.identifier)
    elif detected_device.transport == TransportType.SERIAL:
        return SerialProtocol(port = detected_device.identifier)
    else:
        raise ValueError(f"Unsupported transport type: {detected_device.transport}")