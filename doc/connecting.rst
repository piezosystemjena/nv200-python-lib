Connecting to device
==================================

This section contains guides for how to use the NV200 library.

The NV200 library provides an asynchronous API using :code:`async` and :code:`await`.
That means all functions are non blocking using coroutines.


Discovering Devices
----------------------------

The `nv200.device_discovery` module provides a way to automatically discover all NV200 devices
connected by USB or Ethernet. You just need to call the `discover_devices` function and it will return 
a list of all detected devices.

.. code-block:: python

    from nv200.device_discovery import discover_devices

    async def main_async():
        print("Discovering devices...")
        devices = await discover_devices()
        
        if not devices:
            print("No devices found.")
        else:
            print(f"Found {len(devices)} device(s):")
            for device in devices:
                print(device)


Connecting To a Device
----------------------------

The recommended way to connect to a NV200 device is to use the :func:`create_device_client <nv200.device_interface.create_device_client>`
function from the :mod:`nv200.device_interface` module. So you just need to:

#. Discover devices using the :func:`discover_devices <nv200.device_discovery.discover_devices>` function.
#. Pass the :class:`DeviceProtocol <nv200.device_types.DetectedDevice>` object to the :func:`create_device_client <nv200.device_interface.create_device_client>` function.

.. code-block:: python

    from nv200.device_types import DetectedDevice
    from nv200.device_discovery import discover_devices
    from nv200.device_interface import DeviceClient, create_device_client

    async def main_async():
        print("Discovering devices...")
        detected_devices = await discover_devices()
        
        if not detected_devices:
            print("No devices found.")
            return

        # Create a device client for the first detected device
        device = create_device_client(detected_devices[0])
        await client.connect()



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
    
