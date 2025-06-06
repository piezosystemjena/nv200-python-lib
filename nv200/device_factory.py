from nv200.device_base import DEVICE_MODEL_REGISTRY, PiezoDeviceBase
from nv200.shared_types import DetectedDevice
from nv200.transport_factory import transport_from_detected_device


def create_device_from_id(device_id: str, *args, **kwargs) -> PiezoDeviceBase:
    """
    Creates and returns an instance of a device class corresponding to the given device ID.

    Args:
        device_id (str): The identifier for the device model to instantiate.
        *args: Positional arguments to pass to the device class constructor.
        **kwargs: Keyword arguments to pass to the device class constructor.

    Returns:
        PiezoDeviceBase: An instance of the device class associated with the given device ID.

    Raises:
        ValueError: If the provided device_id is not supported or not found in the registry.
    """
    cls = DEVICE_MODEL_REGISTRY.get(device_id)
    if cls is None:
        raise ValueError(f"Unsupported device ID: {device_id}")
    return cls(*args, **kwargs)



def create_device_from_detected_device(detected_device: DetectedDevice) -> PiezoDeviceBase:
    """
    Creates a device object from the given DetectedDevice parameters.
    """
    if not detected_device:
        raise ValueError("No detected device provided.")

    transport_protcol = transport_from_detected_device(detected_device)
    return create_device_from_id(detected_device.device_id, transport=transport_protcol)
