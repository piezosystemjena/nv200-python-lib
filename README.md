![logo](docs/images/piezosystem_logo.svg)

# NV200 Python Lib

The NV200 Python library allow you to control the NV200 device from piezosystem Jena
via Python. The library supports the ethernet interface as well as the
USB interface of the device.

## Installation

This Python library requires specific dependencies to function correctly.
To ensure that you are using the correct versions of these dependencies,
we recommend setting up a virtual environment. Follow the steps below to 
create a virtual environment and install the required packages using `requirements.txt`.

## Prerequisites

Before starting, make sure you have the following installed:

- Python 3.6 or higher
- `pip` (Python's package installer)

## Step 1: Clone the Repository

Clone the repository to your local machine using the following command:

```bash
git clone http://localhost:10081/piezosystem/nv200_python_lib.git
cd your-repository
```

## Step 2: Create a Virtual Environment

To avoid conflicts with your system's Python packages, it's best to create a virtual 
environment for this library.

- **For Windows:**

```bash
python -m venv .venv
```

- **For macOS/Linux:**

```bash
python3 -m venv .venv
```

This will create a new directory called `.venv` that will contain a clean Python environment.

## Step 3: Activate the Virtual Environment

Once the virtual environment is created, activate it.

- **For Windows:**

```shell
.venv\Scripts\activate
```

- **For macOS/Linux:**

```bash
source venv/bin/activate
```

After activation, your terminal prompt should change to indicate that you are now 
working within the virtual environment.

## Step 4: Install the Dependencies

With the virtual environment active, you can now install the required dependencies 
from the `requirements.txt` file.

Run the following command to install the dependencies:

```bash
pip install -r requirements.txt
```

This will install all the necessary packages listed in the `requirements.txt` file.

## Step 5: Verify Installation

Code into the `src` folder and run the `lantronix_device_discovery.py` file to check,
if the the installation is correct:

```bash
python lantronix_device_discovery.py
```

If no errors occur, the installation is successful!

## Step 6: Deactivate the Virtual Environment (Optional)

When you are done using the library, you can deactivate the virtual environment with the following command:

```bash
deactivate
```

This will return you to your system's global Python environment.

---

## Troubleshooting

- **Error: `pip` command not found:**  
  Ensure that you have Python and `pip` correctly installed. You can check 
  by running `python --version` and `pip --version` in your terminal.

- **Error during installation:**  
  If you run into any issues during the installation of dependencies, ensure that 
  you are using the correct version of Python and that your virtual environment is activated.

