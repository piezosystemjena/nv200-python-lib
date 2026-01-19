# Changelog

All notable changes to this project will be documented in this file.  
This project follows [Semantic Versioning](https://semver.org/).

## [1.6.0] - 2026-01-19
### Added
- **Trigger IO** - added API methods for the NV200 trigger input and output feature

## [1.5.3] - 2025-12-05

### Added
- **SPI Controller Box** - added an API integrating full SPI Box functionality

## [1.5.2] - 2025-10-09
### Improved
- Remove scaling of pcf_a for user transparency

## [1.5.1] - 2025-08-25

### Improved

- added sample time setter to `TimeSeries` class
- added constructor to `WaveformDate` class to allow initialisation of values and sample time

## [1.5.0] - 2025-07-25

### Added

- **Device Param File** - added `DeviceParamFile` for to encapsulate parameter export functionality

### Improved

- **Resonance Measurement** - analysis function now also returns unit of impulse response
- **Impulse Response** - now backs up waveform generator settings when doing impulse measurement
- **Time Series** - added `total_time_ms` function to `TimeSeries` class
- **Actuator Backup** - improved backup function to also export timestamp

### Fixed

- **Logging** - fixed wrong formatting in logger output file

## [1.4.0] - 2025-07-15

### Added

- **Resonance Measurement** - Added `analysis` module with `ResonanceAnalyzer` class for measurement of resonance frequency and spectrum

## [1.3.0] - 2025-07-10

### Added

- **Progress Callback** – Support for progress callback for NV200 waveform upload
- **Help Dictionary** - NV200 help dictionary to get help for commands
- **Waveform Stop** - Stop function to waveform generator
- **Filter Support** - Support fot setting parameters of filters
- **Analog Monitor Source** - Added support for reading and writing analog monitor source
- **Actuator Type** - Support for reading the actuator position sensor type (`PostionSensorType`)
- **Waveforms** - Added support for additional waveforms Triangle and Square
- **Waveform PID Mode** - Support for open loop and closed loop for waveform generator
- **Data Recorder** - Added class methods `get_sample_period_ms_for_duration` and `get_sample_rate_for_duration`

### Improved

- **Documentation** - Improved documentation and updated examples
- **PID Interface** - Moved all PID related functions into `PIDController` class

### Fixed

- **Device Connection** - Fixed `connect_to_single_device` function to properly read device info from detected devices

## [1.2.0] - 2025-06-18

### Added

- **Command Caching** – Added support for command result caching in `device_base.py` to speed up data access.
- **Documentation** – Added a section on actuator configuration backup in Getting Started section
- **Documentation** – Documented cache functionality for the `PiezoDeviceBase` class.

### Fixed

- **Encoding** – Fixed bug by switching to `latin1` encoding (instead of `utf-8`) for data received from the device.

## [1.1.0] - 2025-06-16

### Added

- **Position Reading** Functions to read open loop and closed loop position units
- **Setpoint Range** Function to read `setpoint_range` depending on the current control mode
- **Range Reading** Functions to read position and voltage ranges
- **Actuator Config** Functions to export and import actuator configuration for `NV200Device`
- **Device Flags** Added `ADJUST_COMM_PARAMS` device discovery flag

### Improved

- **Waveform Test** Improved `waveform_generator` test to consider position ranges of the device
- **Timeouts** Increased minimum default communication timeouts from 0.4 to 0.6 seconds
- **Debug Output** Updated debug output messages

### Fixed

- **Device Creation** Fixed device creation in `connection_utils.py` to correctly use `device_factory`

## [1.0.4] - 2025-06-05

### Added

- **Device Discovery** Device discovery for specific devices such as `NV200Device` or `SpiBoxDevice`

### Improved

- Improved documentation and examples

### Fixed

- fixed some small communication bugs

## [1.0.3] - 2025-06-02

### Added

- **connection_utils.py** Added new module connection_utils.py to ease connection to a single device
- **Logging** Added proper logging support using Python logging library

### Improved

- **Device Discovery** Improved device discovery to discover only registered devices
- **Project Structure** Restructured project to improved overall library design

## [1.0.2] - 2025-05-23

### Added

- **data_recorder_example.py** Shows how to use the `data_recorder` module

### Fixed

- renamed `device_types.py` to `shared_types.py` to make the name more clear

## [1.0.1] - 2025-05-22

- First stable version with core functionality.

### Added

- **USB and Ethernet Support** Supports the Ethernet and USB interface of the NV200
- **Device Discovery** Automatically discovers all connected devices
- **Core Device Functionality** Simple Pythonic interface for device control
- **Data Recorder** Supports the NV200 data recorder functionality
- **Waveform Generator** Easy to use functions to access the NV200 Arbitrary Waveform Generator
