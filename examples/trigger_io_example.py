import asyncio

from nv200.nv200_device import NV200Device
from nv200.shared_types import (
    TransportType,
    TriggerInFunction,
    TriggerOutEdge,
    TriggerOutSource,
)
from nv200.connection_utils import connect_to_single_device


async def trigger_io_example():
    """
    Example showing how to configure Trigger In and Trigger Out.
    """
    dev = await connect_to_single_device(NV200Device, TransportType.SERIAL)
    print(f"Connected to device: {dev.device_info}")

    # Determine position range and step size for trigger output configuration
    pos_min, pos_max = await dev.get_position_range()
    span = pos_max - pos_min
    start_pos = pos_min + span * 0.1
    stop_pos = pos_min + span * 0.9
    step_size = max(0.001, span / 10.0)
    if stop_pos - start_pos < step_size:
        step_size = max(0.001, (stop_pos - start_pos) / 2.0)

    # Configure Trigger In (e.g., external trigger starts data recorder)
    await dev.set_trigger_function(TriggerInFunction.DATARECORDER_START)

    # Configure Trigger Out (pulse when setpoint crosses configured steps)
    await dev.set_trigger_output_source(TriggerOutSource.SETPOINT)
    await dev.set_trigger_output_edge(TriggerOutEdge.BOTH)
    await dev.set_trigger_start_position(start_pos)
    await dev.set_trigger_stop_position(stop_pos)
    await dev.set_trigger_step_size(step_size)
    await dev.set_trigger_pulse_length(20)

    print("Trigger configuration:")
    print(f"  Trigger In: {await dev.get_trigger_function()}")
    print(f"  Trigger Out edge: {await dev.get_trigger_output_edge()}")
    print(f"  Trigger Out source: {await dev.get_trigger_output_source()}")
    print(f"  Start position: {await dev.get_trigger_start_position():.4f}")
    print(f"  Stop position: {await dev.get_trigger_stop_position():.4f}")
    print(f"  Step size: {await dev.get_trigger_step_size():.4f}")
    print(f"  Pulse length: {await dev.get_trigger_pulse_length()}")

    # Move the actuator to generate trigger events on the output
    await dev.move_to_position(start_pos)
    await asyncio.sleep(0.3)
    await dev.move_to_position(stop_pos)
    await asyncio.sleep(0.3)

    # Disable Trigger In before disconnecting
    await dev.set_trigger_function(TriggerInFunction.DISABLED)
    await dev.close()

if __name__ == "__main__":
    asyncio.run(trigger_io_example())
