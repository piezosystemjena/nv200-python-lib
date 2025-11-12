API Reference
==================================

The NV200 library API consists of the following modules:

* **Device Discovery and Connection**
  
  * :ref:`device_discovery` — The NV200 device discovery module.
  * :ref:`connection_utils` — Helper functions for device connection.
  * :ref:`device_factory` — Factory for creating device instances from discovery results.

* **Device Abstractions**
  
  * :ref:`device_base` — Generic piezosystem device base class.
  * :ref:`nv200_device` — High-level async client for NV200 piezo controllers.
  * :ref:`spibox_device` — High-level async client for the SPI Controller Box.
  * :ref:`shared_types` — Shared data structures and enums.

* **Transport Protocols**
  
  * :ref:`transport_protocol` — Base class for the device transport protocol.
  * :ref:`serial_protocol` — Serial communication implementation.
  * :ref:`telnet_protocol` — Telnet protocol over Ethernet.

* **Data and Signal Modules**
  
  * :ref:`data_recorder` — Module for recording experimental data.
  * :ref:`waveform_generator` — Interface to arbitrary waveform generator.
  * :ref:`analysis` — Module for resonance analysis

* **Utilities**

  * :ref:`utils` — General utility functions and classes.


Device Discovery and Connection
--------------------------------

device_discovery
^^^^^^^^^^^^^^^^^^^^

.. automodule:: nv200.device_discovery
   :members:
   :show-inheritance:
   :undoc-members:


device_factory
^^^^^^^^^^^^^^^^^^^^

.. automodule:: nv200.device_factory
   :members:
   :show-inheritance:
   :undoc-members:


connection_utils
^^^^^^^^^^^^^^^^^^^^

.. automodule:: nv200.connection_utils
   :members:
   :show-inheritance:
   :undoc-members:


Device Abstractions
------------------------

device_base
^^^^^^^^^^^^^^^^^^^^

.. automodule:: nv200.device_base
   :members:
   :show-inheritance:
   :undoc-members:


nv200_device
^^^^^^^^^^^^^^^^^^^^

.. automodule:: nv200.nv200_device
   :members:
   :show-inheritance:
   :undoc-members:


spibox_device
^^^^^^^^^^^^^^^^^^^^

.. automodule:: nv200.spibox_device
   :members:
   :show-inheritance:
   :undoc-members:


shared_types
^^^^^^^^^^^^^^^^^^^^

.. automodule:: nv200.shared_types
   :members:
   :show-inheritance:


Transport Protocols
----------------------

transport_protocol
^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: nv200.transport_protocol
   :members:
   :show-inheritance:
   :undoc-members:


serial_protocol
^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: nv200.serial_protocol
   :members:
   :show-inheritance:

telnet_protocol
^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: nv200.telnet_protocol
   :members:
   :show-inheritance:

Data and Signal Modules
--------------------------

data_recorder
^^^^^^^^^^^^^^^^

.. automodule:: nv200.data_recorder
   :members:
   :show-inheritance:
   :undoc-members:


waveform_generator
^^^^^^^^^^^^^^^^^^

.. automodule:: nv200.waveform_generator
   :members:
   :show-inheritance:


analysis
^^^^^^^^^^^^^^^^^^

.. automodule:: nv200.analysis
   :members:
   :show-inheritance:


Utilities
--------------------------

utils
^^^^^^^^^^^^^^^^

.. automodule:: nv200.utils
   :members:
   :show-inheritance:
   :undoc-members:
