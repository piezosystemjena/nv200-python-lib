# Changelog

All notable changes to this project will be documented in this file.  
This project follows [Semantic Versioning](https://semver.org/).

## [1.0.4] - 2025-06-05

### Added

- **Device Discovery** Device discovery for specific devices such as NV200Device or SpiBoxDevice

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
