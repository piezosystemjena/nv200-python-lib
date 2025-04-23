from typing import Generator 

class TimeSeries:
    """
    TimeSeries represents waveform data with amplitude values (values) and corresponding sample times (sample_times_ms).
    It also includes a sample time in microseconds.

    Attributes:
        values (List[float]): A list of amplitude values corresponding to the waveform.
        sample_time_us (int): The sampling time in microseconds (i.e., the interval between two time samples).

    Methods:
        values: Returns the amplitude values list.
        generate_sample_times_ms: Returns time (sample_times_ms) values as a generator based on sample_time_us.
        sample_times_ms: Returns time (sample_times_ms) values as a list based on sample_time_us.
    """
    
    def __init__(self, values: list, sample_time_ms: int):
        """
        Initialize the TimeSeries instance with amplitude values and sample time.
        
        Args:
            values (list): The amplitude values corresponding to the waveform.
            sample_time_us (int): The sample time in microseconds (sampling interval).
        """
        self._values = values
        self._sample_time_ms = sample_time_ms

    @property
    def sample_time_ms(self) -> float:
        """Returns the sample time in milliseconds."""
        return self._sample_time_ms
    
    @property
    def values(self) -> list:
        """Return the amplitude values (values) as a list."""
        return self._values

    @values.setter
    def values(self, values: list) -> None:
        """Set the amplitude values (values)."""
        self._values = values

    def generate_sample_times_ms(self) -> Generator[float, None, None]:
        """
        Generator function to return time (sample_times_ms) values as they are requested.
        This will calculate and yield the corresponding time values based on sample_time_us.
        """
        for i in range(len(self.values)):
            yield i * self._sample_time_ms

    @property
    def sample_times_ms(self) -> list:
        """
        Return all time (sample_times_ms) values as a list, calculated based on the sample time.
        """
        return list(self.generate_sample_times_ms())
