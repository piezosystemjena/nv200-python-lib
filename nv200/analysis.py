import numpy as np
import asyncio
from scipy.signal import detrend, find_peaks
from scipy.fft import fft, fftfreq
from nv200.shared_types import PidLoopMode
from nv200.nv200_device import NV200Device
from nv200.data_recorder import DataRecorder, DataRecorderSource, RecorderAutoStartMode
from nv200.waveform_generator import WaveformGenerator, WaveformUnit
from typing import Tuple, Dict


class ResonanceAnalyzer:
    """
    A utility class for measuring and analyzing the resonance behavior of a piezoelectric system.

    This class encapsulates both the hardware interaction needed to acquire an impulse response
    from the device and the signal processing needed to compute the resonance spectrum.
    """

    def __init__(self, device : NV200Device):
        """
        Initializes the ResonanceAnalyzer with the required hardware components.

        Args:
            device: The device object used to restore parameters and get voltage range.
            recorder: The data recorder used to capture the piezo response.
            waveform_generator: The waveform generator used to generate the impulse.
        """
        self.device = device
        self.recorder = DataRecorder(device)
        self.waveform_generator = WaveformGenerator(device)


    async def _backup_resonance_test_parameters(self) -> Dict[str, str]:
        """
        Backs up a predefined list of resonance test settings.
        """
        backup_list = [
            "modsrc", "notchon", "sr", "poslpon", "setlpon", "cl", "reclen", "recstr"]
        return await self.device.backup_parameters(backup_list)
    

    async def _init_resonance_test(self):
        """
        Initializes the device for a resonance test by configuring various hardware settings.

        Raises:
            Any exceptions raised by the underlying device methods.
        """
        dev = self.device
        await dev.pid.set_mode(PidLoopMode.OPEN_LOOP)
        await dev.notch_filter.enable(False)
        await dev.set_slew_rate(2000)
        await dev.position_lpf.enable(False)
        await dev.setpoint_lpf.enable(False)

    
    async def _prepare_recorder(self, duration_ms : float) -> Tuple[float, DataRecorderSource]:
        """
        Prepares the data recorder for recording piezo data for a specified duration.

        Determines the appropriate data source based on the presence of a position sensor,
        configures the recorder with the selected source, sets the autostart mode, and
        recording duration, then starts the recording process.

        Args:
            duration_ms (float): The duration of the recording in milliseconds.

        Returns:
            Tuple[float, DataRecorderSource]: A tuple containing the sample frequency used for recording
            and the data source selected for recording.
        """
        dev = self.device
        recorder = self.recorder
        rec_source = DataRecorderSource.PIEZO_POSITION if await dev.has_position_sensor() else DataRecorderSource.PIEZO_CURRENT_1
        print(f"Recording piezo data from source: {rec_source.name}")
        await recorder.set_data_source(0, rec_source)
        await recorder.set_autostart_mode(RecorderAutoStartMode.START_ON_WAVEFORM_GEN_RUN)
        rec_param = await recorder.set_recording_duration_ms(duration_ms)
        await recorder.start_recording()
        return rec_param.sample_freq, rec_source
    

    async def _prepare_waveform_generator(self, baseline_voltage : float | None) -> list[float]:
        """
        Prepares the waveform generator by creating and setting a waveform with a specified baseline voltage and an impulse.

        This asynchronous method performs the following steps:
        1. Retrieves the voltage range from the device and calculates 10% of the total voltage stroke.
        2. Generates a constant waveform at 2000 Hz with the given baseline voltage.
        3. If no baseline voltage is provided, it retrieves the current piezo voltage.
        4. Sets the value at index 1 of the waveform to the calculated stroke, creating an impulse.
        5. Sets the generated waveform to the waveform generator using voltage units.

        Args:
            baseline_voltage (float): The baseline voltage level for the constant waveform.

        Returns:
            list[float]: A backup of the waveform buffer before setting the new waveform.
        """
        baseline_voltage, impulse_voltage = await self.get_impulse_voltages(baseline_voltage)
        gen = self.waveform_generator        
        waveform = gen.generate_constant_wave(freq_hz=2000, constant_level=baseline_voltage)
        waveform.set_value_at_index(1, impulse_voltage)  # create an impulse
        print(f"Setting waveform with baseline voltage: {baseline_voltage:.3f} V and impulse voltage: {impulse_voltage:.3f} V")
        backup = await gen.read_waveform_buffer(0, waveform.count)
        print(f"Waveform backup: {backup}")
        await gen.set_waveform(waveform, unit=WaveformUnit.VOLTAGE)
        return backup


    async def get_impulse_amplitude(self) -> float:
        """
        Retrieves the voltage amplitude of the impulse generated for impulse response.

        Returns:
            The amplitude of the impulse in volts.
        """
        v_range = await self.device.get_voltage_range()
        amplitude = v_range[1] - v_range[0]
        amplitude *= 0.1 # 10% stroke
        return amplitude


    async def get_impulse_voltages(self, baseline_voltage : float | None = None) -> Tuple[float, float]:
        """
        Retrieves the baseline and impulse voltages for generating the impulse voltage signal.

        Returns:
            Tuple containing:
                - The baseline voltage.
                - The impulse peak voltage
        """
        rec = self.recorder
        if baseline_voltage is None:
            baseline_voltage = await rec.read_single_value_from(DataRecorderSource.PIEZO_VOLTAGE)
        v_max = await self.device.get_max_voltage()
        amplitude = await self.get_impulse_amplitude()
        impulse_voltage = baseline_voltage + amplitude
        if impulse_voltage > v_max:
            impulse_voltage = v_max
            baseline_voltage = v_max - amplitude
        return baseline_voltage, impulse_voltage


    async def measure_impulse_response(self, baseline_voltage : float | None = None) -> Tuple[np.ndarray, float, DataRecorderSource]:
        """
        Measures the impulse response of the system by generating a waveform and
        recording the resulting piezo position signal.

        Returns:
            Tuple containing:
                - The recorded piezo signal as a NumPy array.
                - The sample frequency in Hz.
                - The data source used for recording (e.g., PIEZO_POSITION or PIEZO_CURRENT_1).
        """
        dev = self.device
        gen = self.waveform_generator

        loop_backup = await gen.get_loop_settings()
        backup = await self._backup_resonance_test_parameters()
        await self._init_resonance_test()
        waveform_backup = await self._prepare_waveform_generator(baseline_voltage)

        # prime the system with an initial run
        await gen.start(cycles=1, start_index=0)
        sample_freq, rec_src = await self._prepare_recorder(duration_ms=100)
        
        # start the waveform generator again for recording the impulse response
        await gen.wait_until_finished()
        await gen.start(cycles=1, start_index=0)
        recorder = self.recorder
        await recorder.wait_until_finished()
        rec_data = await recorder.read_recorded_data_of_channel(0)

        # restore device settings and waveform buffer settings
        await dev.restore_parameters(backup)
        await gen.set_waveform_buffer(waveform_backup)
        await gen.configure_waveform_loop(loop_backup["start_index"], loop_backup["loop_start_index"], loop_backup["loop_end_index"])
        
        signal = detrend(np.array(rec_data.values))
        return signal, sample_freq, rec_src


    @staticmethod
    def compute_resonance_spectrum(
        signal: np.ndarray, sample_freq: float
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Computes the frequency spectrum of a signal and extracts the resonance frequency.

        Args:
            signal: The time-domain signal (e.g., piezo position) as a NumPy array.
            sample_freq: The sampling frequency in Hz.

        Returns:
            Tuple containing:
                - Frequencies (xf): NumPy array of frequency bins.
                - Spectrum magnitude (yf): NumPy array of FFT magnitudes.
                - Resonance frequency (res_freq): Peak frequency in Hz.
        """
        # Compute the FFT of the signal
        N = len(signal)

        # Before we do FFT we apply a window function (in this case Hanning window) to reduce spectral leakage
        window = np.hanning(N)
        signal_windowed = signal * window   
        yf = fft(signal_windowed)
        xf = fftfreq(N, 1 / sample_freq)

        # Only keep positive frequencies
        idx = xf > 0
        xf = xf[idx]
        yf = 2.0 * np.abs(np.asarray(yf)[idx]) / N # Normalize the FFT magnitude
 
        # Find the resonance frequency as the peak in the spectrum
        peak_idx, _ = find_peaks(yf, height=np.max(yf) * 0.5) # Find peaks above 50% of max
        res_freq = xf[peak_idx[np.argmax(yf[peak_idx])]] if peak_idx.size else 0.0
  
        return xf, yf, float(res_freq)