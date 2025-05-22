import logging
from device_discovery_sync import discover_devices
from device_interface_sync import DeviceClient, create_device_client


def setup_logging():
    """
    Configures the logging settings for the application.
    """
    logging.basicConfig(
        level=logging.WARN,
        format='%(asctime)s.%(msecs)03d | %(levelname)-6s | %(name)-25s | %(message)s',
        datefmt='%H:%M:%S'
    )

def test_discover_devices():
    """
    Discovers available devices and prints their information.
    """
    logging.getLogger("nv200.device_discovery").setLevel(logging.DEBUG)
    logging.getLogger("nv200.transport_protocols").setLevel(logging.DEBUG)   
    
    print("Discovering devices...")
    devices = discover_devices(full_info=True)
    
    if not devices:
        print("No devices found.")
    else:
        print(f"Found {len(devices)} device(s):")
        for device in devices:
            print(device)
            
    create_device_client(devices[0])
    #create_device_client(devices[0])


if __name__ == "__main__":
    setup_logging()
    test_discover_devices()
