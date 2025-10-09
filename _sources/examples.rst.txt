Examples
==================================

Device Discovery
--------------------

This example demonstrates how to asynchronously discover compatible devices on all available
interfaces. The first discovery is done without extended information, so it is faster, while 
the second discovery includes extended information about the devices, which takes longer.

.. literalinclude:: ../examples/device_discovery_example.py
   :language: python
   :linenos:


The output of the above example can look like this:

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


Serial Connection
--------------------

The example below demonstrates how to establish a serial connection to the NV200/D Compact Amplifier.
Because no serial port is specified, the library will automatically search for available serial ports 
and connect to the first one it finds.

.. literalinclude:: ../examples/serial_connection.py
   :language: python
   :linenos:

This is the expected output of the above example:

.. code-block:: text

    Connected to device on serial port: COM3


Ethernet Connection
--------------------

The example shows, how to manually create a NV200Device instance for a device connected via Ethernet.
Because no IP address is specified, the library will automatically search for available devices
and connect to the first one it finds. 


.. literalinclude:: ../examples/serial_connection.py
   :language: python
   :linenos:

This is the expected output of the above example:

.. code-block:: text

    Connected to device: Telnet @ 192.168.101.4 - NV200/D_NET


Data Recorder
--------------------

The example shows, how to use the data recorder functionality of the NV200/D Compact Amplifier.
It demonstrates how to start and stop the data recorder, as well as how to retrieve recorded data.

.. literalinclude:: ../examples/data_recorder_example.py
   :language: python
   :linenos:

This is the expected output of the above example:

.. code-block:: text

    Running data recorder test...
    Discovering devices connected via USB interface...
    Connected to device: Serial @ COM3 - NV200/D_NET
    Recording parameters:
    Used buffer entries: 2000
    Stride: 1
    Sample frequency (Hz): 20000.0
    Reading recorded data of both channels...

And the created matplotlib figure will look like this:

.. image:: images/data_recorder_matplotlib.png


Waveform Generator
--------------------

The example shows, how to use the arbitrary waveform generator functionality of the NV200/D Compact Amplifier.
It demonstrates how to generate a sine waveform, transfer it to the device, start the waveform generator,
and read back the recorded data.

.. literalinclude:: ../examples/waveform_generator_example.py
   :language: python
   :linenos:

This is the expected output of the above example:

.. code-block:: text

    Generating sine waveform...
    Sample factor 2.0
    Transferring waveform data to device...
    Starting waveform generator...
    Is running: True
    Is running: False
    Reading recorded data of both channels...

And the created matplotlib figure will look like this:

.. image:: images/waveform_generator_matplotlib.png
