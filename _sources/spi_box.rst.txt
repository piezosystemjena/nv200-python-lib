SPI Controller Box
=============================================

To synchronously control multiple NV200 devices, the SPI Box can be used as a master device.
It can send positional data to up to 3 connected NV200 devices via SPI communication.

Due to the NV200's SPI limitations, the SPI Box can only send position commands to the connected devices.
Therefore configuration of the connected NV200 devices (e.g., PID parameters, operation mode, etc.) must be done separately.

The SPI Box provides the following functionality:
- Sending single position commands to up to 3 connected NV200 devices
- Replaying a custom waveform with up to 20000 samples
- Reading back the SPI data received from the connected NV200 devices
- Ethernet, USB and RS-232 connection support

The following example demonstrates how to use these features of the SPI Controller Box.

.. code-block:: python
    import asyncio
    import matplotlib.pyplot as plt

    import matplotlib_helpers
    from nv200.connection_utils import connect_to_detected_device
    from nv200.device_discovery import discover_devices
    from nv200.shared_types import DiscoverFlags
    from nv200.spibox_device import SpiBoxDevice
    from nv200.waveform_generator import WaveformGenerator, WaveformType

    async def spibox_test():
        """
        Asynchronous function to test the functionality of the SPI Box.
        """

        # Discover devices connected via USB interface
        print("Discovering devices connected via USB interface...")
        detected_devices = await discover_devices(
            DiscoverFlags.DETECT_SERIAL | DiscoverFlags.READ_DEVICE_INFO, 
            device_class=SpiBoxDevice
        )
        
        if not detected_devices:
            print("No devices found.")
            return
        
        # connect to the first detected device
        device : SpiBoxDevice = await connect_to_detected_device(detected_devices[0])
        print(f"Connected to device: {device.device_info}")
        
        # Move all channels to lowest and highest setpoints
        print("Moving all channels to lowest setpoints...")
        await device.set_setpoints_percent(0.0, 0.0, 0.0)
        await asyncio.sleep(1.0)

        print("Moving all channels to highest setpoints...")
        await device.set_setpoints_percent(100.0, 100.0, 100.0)
        await asyncio.sleep(1.0)

        positions = await device.get_setpoints_percent()
        print("Channel positions:", positions)


        # Create a waveform generator instance
        # Important: Pass None as device because the SpiBox is no NV200 device
        waveform_generator = WaveformGenerator(None)

        waveforms = []

        # Generate a sine waveforms for all channels
        for ch in range(3):
            waveform = waveform_generator.generate_waveform(
                waveform_type=WaveformType.SINE,
                freq_hz=20,
                low_level=0.0,
                high_level=100.0,
                phase_shift_rad= ch * (3.14159 / 2.0)  # Phase shift each channel by 90 degrees
            )

            waveforms.append(waveform)

        print("Transferring waveforms to device...")
        
        await device.set_waveform_cycles(3, 3, 3)
        await device.set_waveform_sample_factors(
            waveforms[0].sample_factor,
            waveforms[1].sample_factor,
            waveforms[2].sample_factor
        )
        await device.upload_waveform_samples(
            waveforms[0].values,
            waveforms[1].values,
            waveforms[2].values,
            lambda current, total: print(f"Upload progress: {current}/{total} samples")
        )

        # Start waveform output
        await device.start_waveforms()

        print("Waiting for waveform completion...")
        await device.await_waveform_completion()

        # Readback the waveform buffer (every 3rd sample, max 1000 samples)
        response = await device.get_waveform_response(
            3, 
            1000,
            lambda current, total: print(f"Readback progress: {current}/{total} samples")
        )

        # Use matplotlib to plot the recorded data
        matplotlib_helpers.prepare_plot_style()
        plt.plot(response[0].sample_times_ms, response[0].values, linestyle='-', color='orange', label='Channel 1')
        plt.plot(response[1].sample_times_ms, response[1].values, linestyle='-', color='green', label='Channel 2')   
        plt.plot(response[2].sample_times_ms, response[2].values, linestyle='-', color='blue', label='Channel 3')   
        matplotlib_helpers.show_plot()

        await device.close()


Step by step guide to using the SPI Controller Box with the NV200 library
-----------------------------------------------

This guide walks through the typical steps required to control the SPI Controller Box
(`SpiBoxDevice`) using the NV200 Python library and shows how to discover/connect to the device, set simple
setpoints, upload and run waveforms, and read back the SPI response data.

Step by step guide to using the SPI Controller Box with the NV200 library
-----------------------------------------------

Step 1: Import the required modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Start by importing the required modules seen in the example above.

.. code-block:: python

    import asyncio
    import matplotlib.pyplot as plt
    import matplotlib_helpers
    from nv200.connection_utils import connect_to_detected_device
    from nv200.device_discovery import discover_devices
    from nv200.shared_types import DiscoverFlags
    from nv200.spibox_device import SpiBoxDevice
    from nv200.waveform_generator import WaveformGenerator, WaveformType

Step 2: Discover available SPI Box devices
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Discover devices connected via the interfaces you want to use. 
In this example, we search for SPI Controller Boxes connected via USB using:

.. code-block:: python

    detected_devices = await discover_devices(
        DiscoverFlags.DETECT_SERIAL | DiscoverFlags.READ_DEVICE_INFO,
        device_class=SpiBoxDevice
    )

Step 3: Connect to a detected device
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After discovery, connect to a device using the helper from `connection_utils`. In this case we connect to the first detected device:

.. code-block:: python

    device : SpiBoxDevice = await connect_to_detected_device(detected_devices[0])

Step 4: Simple setpoint commands (move channels)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The SPI Box can only send position commands to connected NV200 devices. Use the `SpiBoxDevice`'s high-level set/get
helpers to move channels and read back positions. The example moves all channels to lowest and highest setpoints
and reads them back using:

.. code-block:: python

    await device.set_setpoints_percent(0.0, 0.0, 0.0)
    await asyncio.sleep(1.0)
    await device.set_setpoints_percent(100.0, 100.0, 100.0)
    await asyncio.sleep(1.0)
    positions = await device.get_setpoints_percent()

Note: setpoints are provided as percentages (0.0–100.0). The `SpiBoxDevice` converts these to the NV200 16-bit
hex representation internally.

Step 5: Create waveforms (generator usage)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To replay synchronized motion patterns, create a `WaveformGenerator` instance. The example creates the generator with
`None` as the device because the SPI Box is not a standard `NV200Device` and the generator is only used to create
sample arrays. We then generate three sine waveforms (one per channel) in a loop with `generate_waveform(...)`.

.. code-block:: python

    waveform_generator = WaveformGenerator(None)
    waveforms = []

    # Generate a sine waveforms for all channels
    for ch in range(3):
        waveform = waveform_generator.generate_waveform(
            waveform_type=WaveformType.SINE,
            freq_hz=20,
            low_level=0.0,
            high_level=100.0,
            phase_shift_rad= ch * (3.14159 / 2.0)  # Phase shift each channel by 90 degrees
        )

        waveforms.append(waveform)


Step 6: Transfer waveforms to the SPI Box
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before uploading samples, configure how often the waveforms should repeat and at what sampling rate they should be played back:

.. code-block:: python

    await device.set_waveform_cycles(3, 3, 3)
    await device.set_waveform_sample_factors(
        waveforms[0].sample_factor,
        waveforms[1].sample_factor,
        waveforms[2].sample_factor
    )

Upload the prepared sample arrays with:

.. code-block:: python

    await device.upload_waveform_samples(
        waveforms[0].values,
        waveforms[1].values,
        waveforms[2].values,
        lambda current, total: print(f"Upload progress: {current}/{total} samples")
    )

Step 7: Start and wait for waveform playback
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Start waveform playback on the device with `start_waveforms()` and wait for completion with
`await_waveform_completion()` as shown in the example:

.. code-block:: python

    await device.start_waveforms()
    await device.await_waveform_completion()

Call `await device.stop_waveforms()` if you need to stop playback early.

Step 8: Read back SPI response data (recorded samples)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Read the SPI response buffer using `get_waveform_response`. The example reads every 3rd sample (step size 3) and
limits to 1000 max samples while reporting progress:

.. code-block:: python

    response = await device.get_waveform_response(
        3,
        1000,
        lambda current, total: print(f"Readback progress: {current}/{total} samples")
    )

The returned items are `WaveformGenerator.WaveformData` objects which contain `values` and `sample_time_ms`.

Step 9: Plotting and visualization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the included `matplotlib_helpers` and `matplotlib` to plot response channels as in the example:

.. code-block:: python

    matplotlib_helpers.prepare_plot_style()
    plt.plot(response[0].sample_times_ms, response[0].values, linestyle='-', color='orange', label='Channel 1')
    plt.plot(response[1].sample_times_ms, response[1].values, linestyle='-', color='green', label='Channel 2')
    plt.plot(response[2].sample_times_ms, response[2].values, linestyle='-', color='blue', label='Channel 3')
    matplotlib_helpers.show_plot()

Step 10: Close the device
^^^^^^^^^^^^^^^^^^^^^^^^^^^

When finished, close the device transport to release resources:

.. code-block:: python

    await device.close()

Extra notes and implementation details
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- The `SpiBoxDevice` exposes convenience methods that map to low-level SPI Box commands:
  - `set_waveform_sample_factors(...)` / `get_waveform_sample_factors()`
  - `set_waveform_cycles(...)` / `get_waveform_cycles()`
  - `upload_waveform_samples(...)`, which sets sample counts and issues `wfset` entries for every sample
  - `start_waveforms()` / `stop_waveforms()` which control `wfrun`
  - `get_waveform_response(...)`, `get_response_samples_count()` and `get_response_sample(index)` for readback
- Keep in mind the SPI Box can only send position commands; device configuration (PID, mode, etc.) must be
  applied to the NV200 devices separately using their own configuration flows.


API Reference
-------------

.. automodule:: nv200.spibox_device
   :members:
   :show-inheritance:

