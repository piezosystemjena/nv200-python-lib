from nv200.device_base import PiezoDeviceBase


class SpiBoxDevice(PiezoDeviceBase):
    """
    A high-level asynchronous client for communicating with NV200 piezo controllers.
    This class extends the `PiezoController` base class and provides high-level methods
    for setting and getting various device parameters, such as PID mode, setpoint,
    """
    DEVICE_ID = "SPI Controller Box"