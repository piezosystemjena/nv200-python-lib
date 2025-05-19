# nv200

**Python library for piezosystem NV200 device control**

[![TestPyPI](https://img.shields.io/badge/publish-test--pypi-blue)](https://test.pypi.org/project/nv200/)
[![Python Version](https://img.shields.io/pypi/pyversions/nv200)](https://www.python.org/downloads/)
[![Docs](https://img.shields.io/badge/docs-online-success)](https://nv200-python-lib-e9158a.gitlab.io/)

---

## 📦 Installation

Install from **TestPyPI**:

```bash
pip install --index-url https://test.pypi.org/simple/ nv200
```

If your project depends on packages from the main PyPI index as well, add:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple nv200
```

---

## 🚀 Quick Start

```python
from nv200 import NV200Controller

device = NV200Controller(port="/dev/ttyUSB0")
device.move_absolute(position=50.0)
position = device.query_position()
print(f"Current position: {position} µm")
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
- ✅ Simple Pythonic interface for serial device control
- ✅ Query & set device position
- ✅ Support for real NV200 serial protocol over USB
- ✅ Designed for integration into scientific and automation environments

---

## 📁 Examples

See the `examples/` folder in the repository for:

- Basic device connection
- Position control scripts
- Integration with GUI frameworks (via `PySide6`)

---

## 🧪 Development & Testing

### Install dependencies

```bash
poetry install
```

### Run tests

```bash
poetry run pytest
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
