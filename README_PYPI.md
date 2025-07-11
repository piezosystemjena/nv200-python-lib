# nv200

**Python library for piezosystem NV200 device control**

[![PyPI version](https://img.shields.io/pypi/v/nv200)](https://pypi.org/project/nv200/)
[![Python Version](https://img.shields.io/pypi/pyversions/nv200)](https://www.python.org/downloads/)
[![Docs](https://img.shields.io/badge/docs-online-success)](https://piezosystemjena.github.io/nv200-python-lib/)
![Monthly Downloads](https://img.shields.io/pypi/dm/nv200)

---

## 📦 Installation

Install from **PyPI**:

```shell
pip install nv200
```

---

## 🚀 Quick Start

```python
import asyncio
from nv200.nv200_device import NV200Device
from nv200.shared_types import PidLoopMode
from nv200.connection_utils import connect_to_single_device


async def main_async():
    """
    Moves the device to a specified position using closed-loop control.
    """
    dev = await connect_to_single_device(NV200Device)
    print(f"Connected to device: {dev.device_info}")

    await dev.move_to_position(20)
    await asyncio.sleep(0.2)
    print(f"Current position: {await dev.get_current_position()}")

    # instead of using move_to_position, you can also use two separate commands
    # to set the PID mode and the setpoint
    await dev.set_pid_mode(PidLoopMode.CLOSED_LOOP)
    await dev.set_setpoint(0)
    await asyncio.sleep(0.2)
    print(f"Current position: {await dev.get_current_position()}")


if __name__ == "__main__":
    asyncio.run(main_async())
```

> For more advanced usage and async control, see the full [API documentation](https://piezosystemjena.github.io/nv200-python-lib/).

---

## 📚 Documentation

📖 Full documentation is available at  
👉 **[https://piezosystemjena.github.io/nv200-python-lib/](https://piezosystemjena.github.io/nv200-python-lib/)**

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

The Git repository is available at: https://github.com/piezosystemjena/nv200-python-lib

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
