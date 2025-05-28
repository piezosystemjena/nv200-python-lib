Connecting to device
==================================

Quick Start
----------------------------

Working with a single device
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you work with only one single device, then the quickest way to connect to the deivce is to
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

For a detailed description of the parameters, please refer to the
:func:`API Reference <nv200.connection_utils.connect_to_single_device>` of this function.

.. admonition:: Important
   :class: note

    All device interactions are asynchronous. Make sure to use the `await` keyword
    when calling any asynchronous function, such as `discover_devices()` or
    `client.connect()`. These functions do not block the main thread and allow for
    concurrent operations within an asynchronous application.


Working with multiple devices
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you work with multiple devices, you can use the `discover_devices()` function from the
`nv200.device_discovery` module to discover all devices connected via USB or Ethernetm and then connect
to sepecific or all devices.
The following example shows, how to discover NV200 devices connected via USB or Ethernet
and connect to the first detected device using the asynchronous API.

.. code-block:: python

    import asyncio
    from nv200.device_discovery import discover_devices
    from nv200.nv200_device import NV200Device
    from nv200.shared_types import DiscoverFlags

    async def main():
        print("Discovering devices...")
        devices = await discover_devices(DiscoverFlags.ALL_INTERFACES)

        if not devices:
            print("No devices found.")
            return

        print(f"Found {len(devices)} device(s). Connecting to the first device...")
        client = NV200Device.from_detected_device(devices[0])
        await client.connect()
        print("Connected to device.")

        # Perform your device operations here

        await client.close()
        print("Connection closed.")

    if __name__ == "__main__":
        asyncio.run(main())


If you would like to get some more detailed information about device discovery and connection, please refer to the
next sections.

Discovering Devices
----------------------------

The `nv200.device_discovery` module provides a way to automatically discover all NV200 devices
connected by USB or Ethernet. You just need to call the `discover_devices` function and it will return 
a list of all detected devices.

The `discover_devices` function accepts a `DiscoverFlags` parameter to specify the type of devices to discover.

- Telnet discovery - `DiscoverFlags.DETECT_ETHERNET`
- Serial discovery - `DiscoverFlags.DETECT_SERIAL`
- Device info enrichment - `DiscoverFlags.ENRICH`

The `DiscoverFlags.ENRICH` flag is used to enrich the device information with additional details such as the
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
        devices = await discover_devices(DiscoverFlags.ALL_INTERFACES | DiscoverFlags.EXTENDED_INFO)	
        
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
    Found 2 device(s):
    Telnet @ 192.168.10.178 - Actuator: None #None
    Serial @ COM3 - Actuator: None #None

    Discovering devices with extended information...
    Found 2 device(s):
    Telnet @ 192.168.10.178 - Actuator: TRITOR100SG  #85533
    Serial @ COM3 - Actuator: TRITOR100SG  #85533


Connecting To a Device
----------------------------

The recommended way to connect to a NV200 device is to use the :func:`create_device_client <nv200.device_interface.create_device_client>`
function from the :mod:`nv200.device_interface` module. So you just need to:

#. Discover devices using the :func:`discover_devices <nv200.device_discovery.discover_devices>` function.
#. Pass the :class:`DetectedDevice <nv200.shared_types.DetectedDevice>` object to the :func:`NV200Device.from_detected_device <nv200.nv200_device.from_detected_device>` function.

.. code-block:: python

    import asyncio
    from nv200.shared_types import DetectedDevice
    from nv200.device_discovery import discover_devices
    from nv200.nv200_device import NV200Device

    async def main_async():
        print("Discovering devices...")
        detected_devices = await discover_devices()
        
        if not detected_devices:
            print("No devices found.")
            return

        # Create a device client for the first detected device
        device = NV200Device.from_detected_device(detected_devices[0])
        await device.connect()

    # Running the async main function
    if __name__ == "__main__":
        asyncio.run(main_async())


.. admonition:: Important
   :class: note

    To ensure error-free Ethernet communication with the device, the communication parameters of 
    the XPORT Ethernet interface must be correctly configured, i.e., the flow control mode must 
    be set to `XON_XOFF_PASS_TO_HOST`. This setting is automatically configured when 
    `DeviceClient.connect()` is called.

    To disable the automatic configuration, just call the connect function as follows:

    .. code-block:: python

        await client.connect(auto_adjust_comm_params=False)


Serial Connection to NV200
----------------------------

You can connect to a NV200 device using a serial connection (USB or RS232) by
using :class:`SerialProtocol <nv200.transport_protocols.SerialProtocol>` class. 
Just create the :class:`SerialProtocol <nv200.transport_protocols.SerialProtocol>` 
object and pass it to the :class:`DeviceClient <nv200.device_interface.DeviceClient>` 
constructor.

Auto-detect serial port
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following example shows, how to connect to a NV200 device connected via USB.
The example auto-detects the serial port and connects to the device.
Please note how to use the :code:`await` keyword when calling the asynchronous functions.

.. code-block:: python

    import asyncio
    from nv200.device_interface import DeviceClient
    from nv200.transport_protocols import SerialProtocol

    async def serial_port_auto_detect():
        transport = SerialProtocol()
        client = DeviceClient(transport)
        await client.connect()
        print(f"Connected to device on serial port: {transport.port}")
        await client.close()

    if __name__ == "__main__":
        asyncio.run(serial_port_auto_detect())


Connect to a specific serial port
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to connect to a device on a specific serial port, you can do 
so by specifying the port in the constructor of the :class:`SerialProtocol <nv200.transport_protocols.SerialProtocol>` class.
This is useful if you have multiple devices connected to your computer and 
want to connect to a specific one.

.. code-block:: python

    import asyncio
    from nv200.device_interface import DeviceClient
    from nv200.transport_protocols import SerialProtocol

    async def serial_port_connect():
        transport = SerialProtocol(port="COM3")
        client = DeviceClient(transport)
        await client.connect()
        print(f"Connected to device on serial port: {transport.port}")
        await client.close()

    if __name__ == "__main__":
        asyncio.run(serial_port_connect())


Ethernet Connection to NV200
----------------------------

You can connect to a NV200 device is the same network as your computer using the
:class:`TelnetProtocol <nv200.transport_protocols.TelnetProtocol>` class.
Just create the :class:`TelnetProtocol <nv200.transport_protocols.TelnetProtocol>`
object and pass it to the :class:`DeviceClient <nv200.device_interface.DeviceClient>` 
constructor.

Auto-detect Ethernet connection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following example shows, how to connect to a NV200 device connected via Ethernet.
The example scans all active network interfaces for NV200 devices using a special
UDP device discovery protocol. The function returns as soon as a device is found.

.. code-block:: python

    import asyncio
    from nv200.device_interface import DeviceClient
    from nv200.transport_protocols import TelnetProtocol


    async def ethernet_auto_detect():
        transport = TelnetProtocol()
        client = DeviceClient(transport)
        await client.connect()
        print(f"Connected to device with IP: {transport.host}")
        await client.close()


    if __name__ == "__main__":
        asyncio.run(ethernet_auto_detect())


Ethernet connection to a specific MAC address
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to connect to a device with a specific MAC address, 
you can do so by specifying the MAC address in the constructor of 
the :class:`TelnetProtocol <nv200.transport_protocols.TelnetProtocol>` class.
This is useful if you have multiple devices connected to your network and
want to connect to a specific one.

The following example shows this:

.. code-block:: python

    import asyncio
    from nv200.device_interface import DeviceClient
    from nv200.transport_protocols import TelnetProtocol


    async def ethernet_connect_to_mac():
        transport = TelnetProtocol(MAC="00:80:A3:79:C6:18")
        client = DeviceClient(transport)
        await client.connect()
        print(f"Connected to device with IP: {transport.host}")
        await client.close()


    if __name__ == "__main__":
        asyncio.run(ethernet_connect_to_mac())

    
Ethernet connection to a specific IP address
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to connect to a device with a specific IP address,
you can do so by specifying the IP address in the constructor of 
the :class:`TelnetProtocol <nv200.transport_protocols.TelnetProtocol>` class.

.. code-block:: python

    import asyncio
    from nv200.device_interface import DeviceClient
    from nv200.transport_protocols import TelnetProtocol


    async def ethernet_connect_to_ip():
        transport = TelnetProtocol(host="192.168.10.182")
        client = DeviceClient(transport)
        await client.connect()
        print(f"Connected to device with IP: {transport.host}")
        await client.close()


    if __name__ == "__main__":
        asyncio.run(ethernet_connect_to_ip())
    
