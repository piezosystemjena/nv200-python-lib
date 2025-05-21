# nv200

**Python library for piezosystem NV200 device control**

[![PyPI version](https://img.shields.io/pypi/v/nv200)](https://pypi.org/project/nv200/)
[![Python Version](https://img.shields.io/pypi/pyversions/nv200)](https://www.python.org/downloads/)
[![Docs](https://img.shields.io/badge/docs-online-success)](https://nv200-python-lib-e9158a.gitlab.io/)

---

## 📦 Installation

Install from **PyPI**:

```shell
pip install nv200
```

---

## 🚀 Quick Start

```python
from nv200.device_types import DetectedDevice
from nv200.device_discovery import discover_devices
from nv200.device_interface import DeviceClient, create_device_client

async def main_async():
    print("Discovering devices...")
    detected_devices = await discover_devices()
    
    if not detected_devices:
        print("No devices found.")
        return

    # Create a device client for the first detected device
    device = create_device_client(detected_devices[0])
    await client.connect()

if __name__ == "__main__":
        asyncio.run(main_async())
```

> For more advanced usage and async control, see the full [API documentation](https://nv200-python-lib-e9158a.gitlab.io/).

---

## 📚 Documentation

📖 Full documentation is available at  
👉 **[https://nv200-python-lib-e9158a.gitlab.io/](https://nv200-python-lib-e9158a.gitlab.io/)**

It includes:
- Setup & Installation
- Device Communication Protocols
- Full API Reference
- Examples and Tutorials

---

## 🛠 Features

- ✅ Asynchronous communication via `aioserial` and `telnetlib3`
- ✅ Simple Pythonic interface for device control
- ✅ Query & set device position
- ✅ Supports NV200 data recorder functionality
- ✅ Easy interface for NV200 waveform generator

---

## 📁 Examples

See the `examples/` folder in the repository for:

- Basic device connection
- Position control scripts
- Integration with GUI frameworks (via `PySide6`)

---

## 🧪 Development & Testing

### Git Repository

The Git repository is available at: https://gitlab.com/gitlabuser0xFFFF/nv200_python_lib

### Install dependencies

```bash
poetry install
```

### Build documentation locally

```bash
poetry run build-doc
open doc/_build/index.html
```

---

## 🤝 Contributing

Contributions are welcome! If you encounter bugs or have suggestions:

- Open an issue
- Submit a pull request
- Or contact us directly

For major changes, please open a discussion first.

---

## 📜 License

This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for details.

---

## 👤 Authors

**piezosystemjena GmbH**  
Visit us at [https://www.piezosystem.com](https://www.piezosystem.com)

---

## 🔗 Related

- [Poetry](https://python-poetry.org/)
- [aioserial](https://github.com/chentsulin/aioserial)
- [telnetlib3](https://telnetlib3.readthedocs.io/)
