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