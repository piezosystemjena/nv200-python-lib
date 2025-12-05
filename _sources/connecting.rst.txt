Connecting to device
==================================

Quick Start
----------------------------

Working with a single device
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you work with only one single device, then the quickest way to connect to the device is to
use the `connect_to_single_device()` function from the `nv200.connection_utils` module.
With a single line of code you can discover the device and connect to it.

If no parameters are passed to the function, it will first try to connect to the first device
found via USB, and if no USB device is found, it will try to connect to the first device found via Ethernet.

.. code-block:: python

    from nv200.connection_utils import connect_to_single_device

    async def main():
        device = await connect_to_single_device()
        print("Connected to device.")

        # Perform your device operations here

        await device.close()
        print("Connection closed.")

    if __name__ == "__main__":
        import asyncio
        asyncio.run(main())


If you would like to limit the discovery to a specific interface or if you would like to connect
to a device with a specific MAC address or IP address, you can pass additional parameters to the
function. The following example shows how to connect to a device with a specific MAC address

.. code-block:: python

    from nv200.connection_utils import connect_to_single_device

    async def main():
        device = await connect_to_single_device(TransportType.TELNET, "00:80:A3:79:C6:18")
        # Perform your device operations here
        await device.close()

    if __name__ == "__main__":
        import asyncio
        asyncio.run(main())

Here are some examples of how to use the function:

Auto Discovery
    .. code-block:: python

        device = await nv200.connection_utils.connect_to_single_device()

Serial Port Auto Discovery
    .. code-block:: python

        device = await nv200.connection_utils.connect_to_single_device(TransportType.SERIAL)

Ethernet Auto Discovery
    .. code-block:: python

        device = await nv200.connection_utils.connect_to_single_device(TransportType.TELNET)

Connect to specific MAC address
    .. code-block:: python

        device = await nv200.connection_utils.connect_to_single_device(TransportType.TELNET, "00:80:A3:79:C6:18")

Connect to specific IP address
    .. code-block:: python

        device = await nv200.connection_utils.connect_to_single_device(TransportType.TELNET, "192.168.102.3")

Connect to specific serial port
    .. code-block:: python

        device = await nv200.connection_utils.connect_to_single_device(TransportType.SERIAL, port="COM3")


For a detailed description of the parameters, please refer to the
:func:`API Reference <nv200.connection_utils.connect_to_single_device>` of this function.

.. admonition:: Important
   :class: note

    All device interactions are asynchronous. Make sure to use the ``await`` keyword
    when calling any asynchronous function, such as `connect_to_single_device()`.
    These functions do not block the main thread and allow for
    concurrent operations within an asynchronous application.


Working with multiple devices
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you work with multiple devices, you can use the `discover_devices() <nv200.device_discovery.discover_devices>` 
function from the `nv200.device_discovery` module to discover all devices connected via USB or Ethernet and then connect
to specific or all devices.
The following example shows, how to discover NV200 devices connected via USB or Ethernet
and connect to the first detected device using the asynchronous API.

.. code-block:: python

    import asyncio
    from nv200.device_discovery import discover_devices
    from nv200.connection_utils import connect_to_detected_device
    from nv200.shared_types import DiscoverFlags

    async def main():
        print("Discovering devices...")
        devices = await discover_devices(DiscoverFlags.ALL_INTERFACES | DiscoverFlags.READ_DEVICE_INFO)

        if not devices:
            print("No devices found.")
            return

        print(f"Found {len(devices)} device(s). Connecting to the first device...")
        device = await connect_to_detected_device(devices[0])
        print(f"Connected to device {device.device_info}.")

        # Perform your device operations here

        await device.close()
        print("Connection closed.")

    if __name__ == "__main__":
        asyncio.run(main())

This is the possible output of the example:

.. code-block:: text

    Discovering devices...
    Found 2 device(s). Connecting to the first device...
    Connected to device Telnet @ 192.168.10.180 - NV200/D_NET.
    Connection closed.

.. admonition:: Important
   :class: note

    For the `connect_to_detected_device()` function to work properly, you must first discover the devices 
    using the `DiscoverFlags.READ_DEVICE_INFO` flag. This flag is necessary to enrich the device information with
    additional details such as the name and device type.


Discovering Devices
----------------------------

The `nv200.device_discovery` module provides a way to automatically discover all NV200 devices
connected by USB or Ethernet. You just need to call the `discover_devices() <nv200.device_discovery.discover_devices>` 
function and it will return a list of all detected devices.

The `discover_devices() <nv200.device_discovery.discover_devices>` function accepts a `DiscoverFlags` parameter to 
specify the type of devices to discover.

- Telnet discovery - `DiscoverFlags.DETECT_ETHERNET`
- Serial discovery - `DiscoverFlags.DETECT_SERIAL`
- Device info enrichment - `DiscoverFlags.READ_DEVICE_INFO`

The `DiscoverFlags.READ_DEVICE_INFO` flag is used to enrich the device information with additional details such as the
name and serial number of the actuator connected to the amplifier. This is useful for identifying the device
and its capabilities.

.. code-block:: python

    import asyncio
    from nv200.device_discovery import discover_devices, DiscoverFlags

    async def main_async():
        """
        Asynchronously discovers available devices and prints their information.
        """
        print("\nDiscovering devices...")
        devices = await discover_devices()

        if not devices:
            print("No devices found.")
        else:
            print(f"Found {len(devices)} device(s):")
            for device in devices:
                print(device)

        print("\nDiscovering devices with extended information...")
        devices = await discover_devices(DiscoverFlags.ALL_INTERFACES | DiscoverFlags.READ_DEVICE_INFO)

        if not devices:
            print("No devices found.")
        else:
            print(f"Found {len(devices)} device(s):")
            for device in devices:
                print(device)

    # Running the async main function
    if __name__ == "__main__":
        asyncio.run(main_async())

In this example, there are two discovery calls. The first one discovers all devices but does not 
query the actuator information. The second one discovers all devices and queries the actuator 
information. The output of the example may look like this:

.. code-block:: text

    Discovering devices...
    Found 4 device(s):
    Telnet @ 192.168.101.3 (MAC: 00:80:A3:5A:7F:CB)
    Telnet @ 192.168.101.2 (MAC: 00:80:A3:79:C6:1E)
    Telnet @ 192.168.101.4 (MAC: 00:80:A3:6F:60:F5)
    Serial @ COM5 - SPI Controller Box

    Discovering devices with extended information...
    Found 4 device(s):
    Telnet @ 192.168.101.4 (MAC: 00:80:A3:6F:60:F5) - NV200/D_NET - {'actuator_name': 'PSH15SG_Y   ', 'actuator_serial': '123910'}
    Telnet @ 192.168.101.2 (MAC: 00:80:A3:79:C6:1E) - NV200/D_NET - {'actuator_name': 'PSH20       ', 'actuator_serial': '123910'}
    Telnet @ 192.168.101.3 (MAC: 00:80:A3:5A:7F:CB) - SPI Controller Box
    Serial @ COM5 - SPI Controller Box


Connecting To a Device
----------------------------

The recommended way to connect to a device is to use the `connect_to_detected_device` function from the `nv200.connection_utils` module.
This function takes a `DeviceInfo` object as an argument, which can be obtained from the 
`discover_devices() <nv200.device_discovery.discover_devices>` function.

The following example shows how to connect to the first detected device:

.. code-block:: python

    devices = await discover_devices(DiscoverFlags.ALL_INTERFACES | DiscoverFlags.READ_DEVICE_INFO)

    if not devices:
        print("No devices found.")
        return

    print(f"Found {len(devices)} device(s). Connecting to the first device...")
    device = await connect_to_detected_device(devices[0])

If you would like to separate device object creation from the connection, you can use the `create_device_from_detected_device`
function from the `nv200.device_factory` module to create a device object from the `DeviceInfo` object.
Later you can call the :func:`connect() <nv200.device_base.PiezoDeviceBase>` method on the device object 
to establish the connection:

.. code-block:: python

    import asyncio
    from nv200.device_discovery import discover_devices
    from nv200.device_factory import create_device_from_detected_device
    from nv200.shared_types import DiscoverFlags

    async def main():
        # Detect all device on all interfaces. The DiscoverFlags.READ_DEVICE_INFO flag is used to 
        # enrich the device information -this is required for the create_device_from_detected_device function.
        devices = await discover_devices(DiscoverFlags.ALL_INTERFACES | DiscoverFlags.READ_DEVICE_INFO)

        # Create a device object from the first detected device
        device = create_device_from_detected_device(devices[0])

        # Connect to the device
        await device.connect()

        # Perform your device operations here

        await device.close()

    if __name__ == "__main__":
        asyncio.run(main())
