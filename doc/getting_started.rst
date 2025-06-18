Getting Started with the API
==================================

High-Level Device Functions
-------------------------------

If you have a properly connected `NV200Device` instance, you can start using the API of
the NV200 library. The high-level functions provide a user-friendly interface for common device 
operations such as setting control modes, updating setpoints, or querying the current position. 
They are designed to cover typical use cases and abstract away low-level communication details.

The following example shows, how to position the device in closed loop mode and then
read the current position of the device using the high-level API:

.. code-block:: python

   import asyncio
   from nv200.nv200_device import NV200Device
   from nv200.shared_types import PidLoopMode
   from nv200.connection_utils import connect_to_single_device


   async def move_closed_loop():
      """
      Moves the device to a specified position using closed-loop control.
      """
      dev = await connect_to_single_device(NV200Device)
      print(f"Connected to device: {dev.device_info}")

      await dev.move_to_position(20)
      await asyncio.sleep(0.2)
      print(f"Current position: {await dev.get_current_position()}")

      # instead of using move_to_position, you can also use two separate commands
      # to set the PID mode and the setpoint
      await dev.set_pid_mode(PidLoopMode.CLOSED_LOOP)
      await dev.set_setpoint(0)
      await asyncio.sleep(0.2)
      print(f"Current position: {await dev.get_current_position()}")


   if __name__ == "__main__":
      asyncio.run(move_closed_loop())


Generic Read/Write Methods
-----------------------------

These methods offer low-level access to the device's command interface.
They are useful for advanced users who need direct control or want to access features not 
covered by the high-level API. Some of the generic methods are:

- :meth:`write() <nv200.device_interface.DeviceClient.write>`
- :meth:`read() <nv200.device_interface.DeviceClient.read>`
- :meth:`read_response() <nv200.device_interface.DeviceClient.read_response>`
- :meth:`read_values() <nv200.device_interface.DeviceClient.read_values>`
- :meth:`read_float_value() <nv200.device_interface.DeviceClient.read_float_value>`
- :meth:`read_int_value() <nv200.device_interface.DeviceClient.read_int_value>`
- :meth:`read_string_value() <nv200.device_interface.DeviceClient.read_string_value>`

The following example shows how to use the generic read/write methods to read and write
device parameters in a generic low-level way:


.. code-block:: python

   import asyncio
   from nv200.nv200_device import NV200Device
   from nv200.connection_utils import connect_to_single_device

   async def read_write_tests():
      """
      Test some generic low-level read/write methods
      """
      dev = await connect_to_single_device(NV200Device)
      print(f"Connected to device: {dev.device_info}")
      await dev.write('cl,0')
      response = await dev.read_response_string('cl')
      print(repr(response))
      response = await dev.read_response('set')
      print(response)
      response = await dev.read_values('recout,0,0,1')
      print(response)
      response = await dev.read_float_value('set')
      print(response)
      response = await dev.read_int_value('cl')
      print(response)
      response = await dev.read_string_value('desc')
      print(response)
      await dev.close()


   if __name__ == "__main__":
      asyncio.run(read_write_tests())

The expected output of the above example is:

.. code-block:: text

   Connected to device: Telnet @ 192.168.101.2 - NV200/D_NET
   'cl,0\r\x00\n'
   ('set', ['0.000'])
   ['0', '0', '2.580']
   0.0
   0
   PSH20  

So if you do not find a specific function in the high-level API, you can use the generic read/write methods
to access the device parameters directly. The generic methods are also useful for debugging purposes.

Command Parameter Caching
------------------------------------

The ``PiezoDeviceBase`` class provides an optional **command result caching** mechanism to optimize read 
performance for piezoelectric device communication. This section explains the purpose of this cache, 
how to control it, when to use it, and provides usage examples.

Purpose of the Cache
^^^^^^^^^^^^^^^^^^^^^^^^

The piezoelectric devices such as the NV200/D are accessed via transport protocols like **serial** or **telnet**, 
which can introduce communication latency. When applications (e.g., GUIs) frequently request the same values 
(such as current position, mode, or configuration), re-reading those values over the wire can become inefficient.

The caching mechanism in `PiezoDeviceBase` stores the result of frequently-read commands locally. 
If caching is enabled and a requested command is cached, the device will **not** be queried again—instead, 
the cached value will be returned immediately. This is especially useful for:

- Polling the same parameter at high frequency
- Avoiding redundant communication
- Reducing delays in latency-sensitive applications

.. note::
   
   Caching only applies to commands that are explicitly marked as cacheable in the concrete 
   device class (see below) - that means it only applies to commands that are defined in the
   `CACHEABLE_COMMANDS` set of the concrete device class.


How to Enable or Disable the Cache
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Caching is controlled via the class variable `CMD_CACHE_ENABLED`:

.. code-block:: python

    PiezoDeviceBase.CMD_CACHE_ENABLED = True  # or False

When set to ``True`` (default), caching is enabled for all cacheable commands defined in the concrete device's 
`CACHEABLE_COMMANDS` set. When ``False``, all caching behavior is disabled globally.

You can override this at runtime:

.. code-block:: python

   import asyncio
   from nv200.connection_utils import connect_to_single_device
   from nv200.nv200_device import NV200Device
   from nv200.device_base import PiezoDeviceBase

   async def main_async():
      device = await connect_to_single_device(NV200Device)
      PiezoDeviceBase.CMD_CACHE_ENABLED = False  # disable globally
      pidmode = await device.get_pid_mode() # always reads from device
      print(pidmode)

      PiezoDeviceBase.CMD_CACHE_ENABLED = True  # enable globally
      pidmode = await device.get_pid_mode()  # uses cache if available
      print(pidmode)

   # Running the async main function
   if __name__ == "__main__":
      asyncio.run(main_async())


When to Enable or Disable the Cache
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**✅ Enable the cache when:**

- Your application is the **only** process accessing the device.
- Values you read do not change unexpectedly - such as read-only like maximum or minimum position
- You want to improve performance or reduce traffic.

**❌ Disable the cache when:**

- Multiple applications or users are interacting with the same device.
- Device values may change outside your control (e.g., via a serial console).
- You need guaranteed up-to-date values on each read.

.. note::

    If there is *any* chance that another process modifies the device state in parallel, 
    caching should be **disabled** to avoid serving outdated values.



Clearing the Command Cache
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can clear the local cache manually using the `clear_cmd_cache()` method. This is useful if:

- You suspect the cache is stale.
- You've temporarily disabled caching and want to refresh once re-enabled.
- You know the device state has changed externally and need to invalidate local values.

.. code-block:: python

    await device.get_max_position()         # This will be cached
    device.clear_cmd_cache()                # Clear the cache
    await device.device.get_max_position()  # This forces a re-read from the device


Summary
-------

Caching in `PiezoDeviceBase` is a powerful tool to reduce communication overhead and
latency when interacting with piezo devices. `CMD_CACHE_ENABLED` provides a simple global 
toggle, and all commands listed in `CACHEABLE_COMMANDS` in each concrete subclass will
automatically benefit from caching when enabled.
