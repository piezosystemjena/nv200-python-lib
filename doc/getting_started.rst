Getting Started with the API
==================================

High-Level Device Functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have a properly connected `DeviceClient` instance, you can start using the API of
the NV200 library. The high-level functions provide a user-friendly interface for common device 
operations such as setting control modes, updating setpoints, or querying the current position. 
They are designed to cover typical use cases and abstract away low-level communication details.

The following example shows, how to position the device in closed loop mode and then
read the current position of the device using the high-level API:

.. code-block:: python

      import asyncio
      from nv200.device_interface import DeviceClient, PidLoopMode, StatusFlags

      async def move_closed_loop(client: DeviceClient):
         await client.move_to_position(80)
         await asyncio.sleep(0.2)
         print(f"Current position: {await client.get_current_position()}")

         # instead of using move_to_position, you can also use two separate commands
         # to set the PID mode and the setpoint
         await client.set_pid_mode(PidLoopMode.CLOSED_LOOP)
         await client.set_setpoint(0)
         await asyncio.sleep(0.2)
         print(f"Current position: {await client.get_current_position()}")

      if __name__ == "__main__":
         asyncio.run(move_closed_loop())


Generic Read/Write Methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
   from nv200.device_interface import DeviceClient
   from nv200.transport_protocols import SerialProtocol

   async def read_write_tests():
      """
      Test some generic low-level read/write methods
      """
      transport = SerialProtocol(port="COM3")
      device_client = DeviceClient(transport)
      await device_client.connect()
      print(f"Connected to device on serial port: {transport.port}")
      await device_client.write('cl,0')
      response = await device_client.read('cl')
      print(response)
      response = await device_client.read_response('set')
      print(response)
      response = await device_client.read_values('recout,0,0,1')
      print(response)
      response = await device_client.read_float_value('set')
      print(response)
      response = await device_client.read_int_value('cl')
      print(response)
      response = await device_client.read_string_value('desc')
      print(response)
      await device_client.close()


   if __name__ == "__main__":
      asyncio.run(read_write_tests())

The expected output of the above example is:

.. code-block:: text

   Connected to device on serial port: COM3
   b'cl,0\r\n'
   ('set', ['111.011'])
   ['0', '0', '0.029']
   111.011
   0
   TRITOR100SG 

So if you do not find a specific function in the high-level API, you can use the generic read/write methods
to access the device parameters directly. The generic methods are also useful for debugging purposes.