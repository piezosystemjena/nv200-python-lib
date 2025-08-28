import asyncio
import numpy as np
import matplotlib.pyplot as plt

from nv200.nv200_device import NV200Device 
from nv200.shared_types import TransportType
from nv200.analysis import ResonanceAnalyzer
from nv200.connection_utils import connect_to_single_device

import matplotlib_helpers


async def resonance_measurement_test():
    """
    Performs a resonance measurement test on a connected NV200 device.
    This asynchronous function connects to a single NV200 device via serial port, measures its impulse response,
    computes the resonance spectrum, and visualizes the results using matplotlib. The impulse response and resonance
    spectrum are plotted in separate subplots, with appropriate axis labels and styling.
    
    Steps performed:
        1. Connects to the NV200 device using serial transport.
        2. Measures the impulse response using the ResonanceAnalyzer.
        3. Computes the resonance spectrum from the impulse response.
        4. Retrieves the position unit from the device for labeling.
        5. Plots the impulse response and resonance spectrum in a two-row subplot.
    """
    # Connect to the one and only NV200 device connected via serial port
    dev = await connect_to_single_device(NV200Device, TransportType.SERIAL)

    # Create resonance analyzer for the connected device
    analyzer = ResonanceAnalyzer(dev)

    # first measure impulse response and then use it to compute the resonance spectrum
    signal, sample_freq, rec_src = await analyzer.measure_impulse_response()
    xf, yf, res_freq = ResonanceAnalyzer.compute_resonance_spectrum(signal, sample_freq)

    # Get the position unit from the device for showing the unit in the plot
    unit = await dev.get_position_unit()

    # Use matplotlib to plot the recorded data
    t = np.arange(len(signal)) / sample_freq  # time in seconds
    
    # Create figure with 2 subplots (rows=2, cols=1)
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=False)

    # Plot impulse response into first subplot
    ax1.plot(t, signal, color=(0.0, 1.0, 0.0), label='Impulse Response')
    ax1.set_xlabel("Time (ms)")
    ax1.set_ylabel(f"Piezo Position ({unit})")
    ax1.set_title("Impulse Response")
    matplotlib_helpers.prepare_axes_style(ax1)

    # Plot frequency spectrum into second subplot
    ax2.plot(xf, yf, color='r', label='Frequency Spectrum')
    ax2.axvline(float(res_freq), color='orange', linestyle='--', label=f'Resonance: {float(res_freq):.1f} Hz')
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel(f"Amplitude ({unit})")
    ax2.set_title("Resonance Spectrum")
    ax2.set_xlim(10, 4000)
    matplotlib_helpers.prepare_axes_style(ax2)
  
    plt.tight_layout()
    plt.show(block=True)


if __name__ == "__main__":
    print("Running resonance measurement test...")
    asyncio.run(resonance_measurement_test())
