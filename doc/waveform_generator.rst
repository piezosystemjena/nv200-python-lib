Waveform Generator
----------------------------

If a device provides waveform generator functionality, such as the NV200 amplifier, you can use the
:class:`WaveformGenerator <nv200.waveform_generator.WaveformGenerator>` class to access this functionality.
For example the NV200 provides an arbitrary waveform generator that can be used to generate a variety of waveforms.
The arbitrary waveform generator can generate a single or repetitive setpoint signal. The curve shape 
can be freely defined by up to 1024 samples.

The following example demonstrates how to use the :mod:`nv200.waveform_generator` module with the
`DeviceClient` from the `nv200.device_interface`. It covers setting up the `WaveformGenerator`, 
generating a sine wave, and starting the waveform generator.

.. code-block:: python

   import asyncio
   from nv200.device_interface import DeviceClient
   from nv200.transport_protocols import TelnetProtocol
   from nv200.waveform_generator import WaveformGenerator

   async def waveform_generator_test():
      # Create the device client using Telnet protocol
      transport = TelnetProtocol(MAC="00:80:A3:79:C6:18")  
      client = DeviceClient(transport)
      await client.connect()

      # Initialize the waveform generator with the device client
      waveform_generator = WaveformGenerator(client)

      # Generate a sine wave with a frequency of 1 Hz, low level of 0, and high level of 80 µm
      sine = waveform_generator.generate_sine_wave(freq_hz=1, low_level=0, high_level=80)
      print(f"Sample factor {sine.sample_factor}")

      # Transfer the waveform data to the device
      await waveform_generator.set_waveform(sine)

      # Start the waveform generator with 1 cycle and starting index of 0
      await waveform_generator.start(cycles=1, start_index=0)

      # Wait until the waveform generator finishes the move
      await waveform_generator.wait_until_finished()

      # Close the device client connection
      await client.close()

   if __name__ == "__main__":
      asyncio.run(waveform_generator_test())

Step by step guide to using the Waveform Generator
==================================================

This guide will walk you through the steps to set up and use the waveform generator using the given
example code.

Step 1: Import Necessary Modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To get started, you'll need to import the relevant modules. 
The `WaveformGenerator` class is imported from the `nv200.waveform_generator` module,
along with other necessary components such as `DeviceClient` and `TelnetProtocol`.

.. code-block:: python

   import asyncio
   from nv200.device_interface import DeviceClient
   from nv200.transport_protocols import TelnetProtocol
   from nv200.waveform_generator import WaveformGenerator


Step 2: Create the DeviceClient
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To interact with the NV200 device, you must create a `DeviceClient` 
instance. This client communicates with the device using the `TelnetProtocol`, 
which requires the device's MAC address for connection.

.. code-block:: python

   # Create the device client using Telnet protocol
   transport = TelnetProtocol(MAC="00:80:A3:79:C6:18")  
   client = DeviceClient(transport)
   await client.connect()


Step 3: Initialize the Waveform Generator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After setting up the device client, initialize the `WaveformGenerator` with the 
device client instance. This allows you to interact with the waveform generation 
functionality.

.. code-block:: python

   # Initialize the waveform generator with the device client
   waveform_generator = WaveformGenerator(client)


Step 4: Generate the Waveform
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In this example, we will generate a sine wave using the `generate_sine_wave` method of 
the `WaveformGenerator` class. You can specify the frequency, low level (minimum value), 
and high level (maximum value) of the sine wave. Optionally, you can also apply a 
phase shift to the waveform.

.. code-block:: python

   # Generate a sine wave with a frequency of 1 Hz, low level of 0, and high level of 80 µm
   sine = waveform_generator.generate_sine_wave(freq_hz=1, low_level=0, high_level=80)
   print(f"Sample factor {sine.sample_factor}")

Step 5: Transfer the Waveform to the Device
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once the sine wave has been generated, you need to transfer the waveform data to the device. 
The `set_waveform` method is used for this purpose, which takes in the generated waveform data 
and uploads it to the connected device.

.. code-block:: python

   # Transfer the waveform data to the device
   await waveform_generator.set_waveform(sine)

.. admonition:: Important
   :class: note

   Transferring the waveform data to the device may take some seconds, depending on the size of the
   waveform. Ensure that you wait for the transfer to complete before proceeding with any further
   operations.


Step 6: Start the Wavform Generator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With the waveform data uploaded to the device, you can now start the waveform generator. 
You can specify the number of cycles for the waveform to repeat and the starting index of 
the waveform data. In this example, we are starting the generator with one cycle, using an index of 0.

.. code-block:: python

   # Start the waveform generator with 1 cycle and starting index of 0
   await waveform_generator.start(cycles=1, start_index=0)


Step 7: Wait for the Waveform to Finish
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After starting the waveform generator, you can wait for the waveform to finish its cycle.
The `WaveformGenerator.wait_until_finished` method can be used to wait until the waveform generator has 
completed its operation. It waits until the `is_running` function returns false.

.. code-block:: python

   # Wait until the waveform generator finishes the move
   await waveform_generator.wait_until_finished()

Step 8: Close the Device Client Connection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once the waveform has finished executing, it is good practice to close the connection
to the device to free up resources.

.. code-block:: python

   # Close the device client connection
   await client.close()


API Reference
==============
.. automodule:: nv200.waveform_generator
   :members:
   :show-inheritance:
   :undoc-members: