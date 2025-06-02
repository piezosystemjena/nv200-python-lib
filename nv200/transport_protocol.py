"""
This module defines the transport protocols for communicating with NV200 devices, including Telnet and Serial interfaces.

Classes:
    - :class:`.TransportProtocol`: Abstract base class for transport protocols.
    - :class:`.TelnetProtocol`: Implements Telnet-based communication with NV200 devices.
    - :class:`.SerialProtocol`: Implements serial communication with NV200 devices.

Example:
    .. code-block:: python

        import asyncio
        from nv200.device_interface import DeviceClient
        from nv200.transport_protocols import SerialProtocol

        async def serial_port_auto_detect():
            transport = SerialProtocol()
            client = DeviceClient(transport)
            await client.connect()
            print(f"Connected to device on serial port: {transport.port}")
            await client.close()

        if __name__ == "__main__":
            asyncio.run(serial_port_auto_detect())

"""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Awaitable, Optional
from nv200.shared_types import DetectedDevice, TransportProtocolInfo

if TYPE_CHECKING:
    from nv200.device_base import PiezoDeviceBase


# Global module locker
logger = logging.getLogger(__name__)

# An async function taking a TransportProtocol and returning nothing
DiscoveryCallback = Callable[["TransportProtocol", "DetectedDevice"], Awaitable[None]]


class TransportProtocol(ABC):
    """
    Abstract base class representing a transport protocol interface for a device.
    """
    XON = b'\x11'
    XOFF = b'\x13'
    LF = b'\x0A'
    CR = b'\x0D'
    CRLF = b'\x0D\x0A'
    DEFAULT_TIMEOUT_SECS = 0.4
    rx_delimiter = XON  # Default delimiter for reading messages

    @abstractmethod
    async def connect(self, auto_adjust_comm_params: bool = True, device : Optional['PiezoDeviceBase'] = None):
        """
        Establishes an asynchronous connection to the NV200 device.

        This method is intended to handle the initialization of a connection
        to the NV200 device. The implementation should include the necessary
        steps to ensure the connection is successfully established.

        Raises:
            Exception: If the connection fails or encounters an error.
        """

    async def read_message(self, timeout : float = DEFAULT_TIMEOUT_SECS) -> str:
        """
        Asynchronously reads a complete delimited message from the device

        Returns:
            str: The response read from the source.
        """
        return await self.read_until(self.rx_delimiter, timeout)

    @abstractmethod
    async def read_until(self, expected: bytes = XON, timeout : float = DEFAULT_TIMEOUT_SECS) -> str:
        """
        Asynchronously reads data from the connection until the specified expected byte sequence is encountered.

        Args:
            expected (bytes, optional): The byte sequence to read until. Defaults to serial.XON.

        Returns:
            str: The data read from the serial connection, decoded as a string, .
        """

    @abstractmethod
    def get_info(self) -> TransportProtocolInfo:
        """
        Returns metadata about the transport protocol, such as type and identifier.
        """

    @abstractmethod
    async def flush_input(self):
        """
        Asynchronously flushes or clears the input buffer of the transport protocol.

        This method is intended to remove any pending or unread data from the input stream,
        ensuring that subsequent read operations start with a clean buffer. It is typically
        used to prevent processing of stale or unwanted data.
        """

    @abstractmethod
    async def write(self, cmd: str):
        """
        Sends a command to the NV200 device asynchronously.

        Args:
            cmd (str): The command string to be sent to the device.

        Raises:
            Exception: If there is an error while sending the command.
        """

    @abstractmethod
    async def close(self):
        """
        Asynchronously closes the connection or resource associated with this instance.

        This method should be used to release any resources or connections
        that were opened during the lifetime of the instance. Ensure that this
        method is called to avoid resource leaks.

        Raises:
            Exception: If an error occurs while attempting to close the resource.
        """


