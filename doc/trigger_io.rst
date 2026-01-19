Trigger In and Trigger Out
=============================

The NV200 provides Trigger In and Trigger Out signals that can be used to synchronize
waveform playback, data recording, or external equipment. Trigger In selects what the
device should do when it receives an external trigger. Trigger Out generates pulses
based on a selected signal source (position or setpoint) and user-defined thresholds.

The following example demonstrates how to configure Trigger In and Trigger Out on an
:class:`NV200Device <nv200.nv200_device.NV200Device>`. It sets up an external trigger to
start the data recorder and configures Trigger Out pulses based on the setpoint.

.. code-block:: python

   import asyncio
   from nv200.nv200_device import NV200Device
   from nv200.shared_types import TriggerInFunction, TriggerOutEdge, TriggerOutSource, TransportType
   from nv200.connection_utils import connect_to_single_device

   async def trigger_io_example():
      device = await connect_to_single_device(NV200Device, TransportType.SERIAL)

      # Trigger In: start the data recorder when an external trigger arrives
      await device.set_trigger_function(TriggerInFunction.DATARECORDER_START)

      # Trigger Out: pulse when setpoint crosses the configured steps
      await device.set_trigger_output_source(TriggerOutSource.SETPOINT)
      await device.set_trigger_output_edge(TriggerOutEdge.BOTH)
      await device.set_trigger_start_position(10.0)
      await device.set_trigger_stop_position(80.0)
      await device.set_trigger_step_size(5.0)
      await device.set_trigger_pulse_length(20)

      await device.close()

   if __name__ == "__main__":
      asyncio.run(trigger_io_example())


Step by step guide to using Trigger I/O
------------------------------------------

This guide walks you through configuring Trigger In and Trigger Out with the NV200.

Step 1: Import Necessary Modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Import the device class and the trigger enums from :mod:`nv200.shared_types`.

.. code-block:: python

   import asyncio
   from nv200.nv200_device import NV200Device
   from nv200.shared_types import TriggerInFunction, TriggerOutEdge, TriggerOutSource, TransportType
   from nv200.connection_utils import connect_to_single_device


Step 2: Connect to the device
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Connect to the first available NV200 device.

.. code-block:: python

   device = await connect_to_single_device(NV200Device, TransportType.SERIAL)


Step 3: Configure Trigger In
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Select the action the device should perform when an external trigger is received.
The available functions are defined in :class:`TriggerInFunction <nv200.shared_types.TriggerInFunction>`.

.. code-block:: python

   await device.set_trigger_function(TriggerInFunction.DATARECORDER_START)


Step 4: Configure Trigger Out
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Select the Trigger Out source and edge, then define start/stop positions and step size.
These positions are in the device position units (for closed-loop actuators) or voltage
(for open-loop actuators). The pulse length is given in samples.

.. code-block:: python

   await device.set_trigger_output_source(TriggerOutSource.SETPOINT)
   await device.set_trigger_output_edge(TriggerOutEdge.BOTH)
   await device.set_trigger_start_position(10.0)
   await device.set_trigger_stop_position(80.0)
   await device.set_trigger_step_size(5.0)
   await device.set_trigger_pulse_length(20)

.. admonition:: Important
   :class: note

   The start/stop positions must lie within the device movement range, and the
   step size must be greater than zero. For details, see the NV200 manual and the
   corresponding methods on :class:`NV200Device <nv200.nv200_device.NV200Device>`.


Step 5: Close the device connection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Close the connection when you are done.

.. code-block:: python

   await device.close()


API Reference
--------------

You will find a detailed description of the API methods in the
:ref:`API Reference <nv200_device>` and the trigger enums in :ref:`shared_types`.
