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

    It requires instances of the device interface, data recorder, and waveform generator to
    coordinate the measurement. The class is designed to separate hardware orchestration from
    signal analysis logic.
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

    
    async def _prepare_recorder(self, duration_ms : float) -> float:
        """
        Prepares and starts the data recorder for a specified duration to record the
        impulse response of the piezo position.

        Returns:
            The sample frequency in Hz of the recorded data.
        """
        recorder = self.recorder
        await recorder.set_data_source(0, DataRecorderSource.PIEZO_POSITION)
        await recorder.set_autostart_mode(RecorderAutoStartMode.START_ON_WAVEFORM_GEN_RUN)
        rec_param = await recorder.set_recording_duration_ms(duration_ms)
        await recorder.start_recording()
        return rec_param.sample_freq
    

    async def _prepare_waveform_generator(self, baseline_voltage : float):
        """
        Prepares the waveform generator by creating and setting a waveform with a specified baseline voltage and an impulse.

        This asynchronous method performs the following steps:
        1. Retrieves the voltage range from the device and calculates 10% of the total voltage stroke.
        2. Generates a constant waveform at 2000 Hz with the given baseline voltage.
        3. Sets the value at index 1 of the waveform to the calculated stroke, creating an impulse.
        4. Sets the generated waveform to the waveform generator using voltage units.

        Args:
            baseline_voltage (float): The baseline voltage level for the constant waveform.
        """
        dev = self.device
        v_range = await dev.get_voltage_range()
        stroke = v_range[1] - v_range[0]
        stroke *= 0.1 # 10 stroke
    
        gen = self.waveform_generator
        waveform = gen.generate_constant_wave(freq_hz=2000, constant_level=baseline_voltage)
        waveform.set_value_at_index(1, stroke)  # create an impulse
        await gen.set_waveform(waveform, unit=WaveformUnit.VOLTAGE)


    async def measure_impulse_response(self, baseline_voltage : float) -> Tuple[np.ndarray, float]:
        """
        Measures the impulse response of the system by generating a waveform and
        recording the resulting piezo position signal.

        Returns:
            Tuple containing:
                - The recorded piezo signal as a NumPy array.
                - The sample frequency in Hz.
        """
        dev = self.device

        backup = await self._backup_resonance_test_parameters()
        await self._init_resonance_test()
        await self._prepare_waveform_generator(baseline_voltage)

        # prime the system with an initial run
        gen = self.waveform_generator
        await gen.start(cycles=1, start_index=0)
        sample_freq = await self._prepare_recorder(duration_ms=100)
        
        # start the waveform generator again for recording the impulse response
        await gen.wait_until_finished()
        await gen.start(cycles=1, start_index=0)
        recorder = self.recorder
        await recorder.wait_until_finished()
        rec_data = await recorder.read_recorded_data_of_channel(0)

        await dev.restore_parameters(backup)
        
        signal = detrend(np.array(rec_data.values))
        return signal, sample_freq


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
        yf = fft(signal)
        xf = fftfreq(N, 1 / sample_freq)

        # Only keep positive frequencies
        idx = xf > 0
        xf = xf[idx]
        yf = np.abs(np.asarray(yf)[idx])  # Normalize the FFT magnitude

        # Find the resonance frequency as the peak in the spectrum
        peak_idx, _ = find_peaks(yf, height=np.max(yf) * 0.5) # Find peaks above 50% of max
        res_freq = xf[peak_idx[np.argmax(yf[peak_idx])]]

        return xf, yf, float(res_freq)