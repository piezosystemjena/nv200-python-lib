import asyncio
import telnetlib3
import logging
from typing import Optional, List
from nv200.transport_protocol import TransportProtocol
import nv200.lantronix_xport as xport
from nv200.shared_types import NetworkEndpoint, DetectedDevice, TransportType, DiscoverFlags, TransportProtocolInfo
from nv200.device_base import PiezoDeviceBase

# Global module locker
logger = logging.getLogger(__name__)

class TelnetProtocol(TransportProtocol):
    """
    TelnetTransport is a class that implements a transport protocol for communicating
    with piezosystem devices over Telnet. It provides methods to establish a connection,
    send commands, read responses, and close the connection.
    """
    __host : str
    __MAC : str
    __port : int
    
    def __init__(self, host: str = "", port: int = 23, MAC: str = ""):
        """
        Initializes the transport protocol.

        Args:
            host (str, optional): The hostname or IP address of the NV200 device. Defaults to None.
            port (int, optional): The port number to connect to. Defaults to 23.
            MAC (str, optional): The MAC address of the NV200 device. Defaults to None.
        """
        self.__host = host
        self.__port = port
        self.__MAC = MAC
        self.__reader = None
        self.__writer = None


    async def __connect_telnetlib(self):
        """
        Connect to telnetlib3 library
        """
        self.__reader, self.__writer = await asyncio.wait_for(
            telnetlib3.open_connection(self.__host, self.__port),
            timeout=5
        )        


    async def is_xon_xoff_forwared_to_host(self) -> bool:
        """
        Checks if XON/XOFF flow control is forwarded to the host.

        This method sends a command to the device and checks the response to determine
        if XON/XOFF flow control is enabled. The detection is based on whether the
        response starts with the byte sequence "XON/XOFF".

        Returns:
            bool: True if XON/XOFF flow control is forwarded to the host, False otherwise.
        """
        await self.write('\r\n')
        await asyncio.sleep(0.1)
        response = await self.__reader.read(1024)
        return response.startswith('\x13')
    
    @staticmethod
    async def configure_flow_control_mode(host: str) -> bool:
        """
        Configures the flow control mode for the device to pass XON/XOFF characters to host
        """
        return await xport.configure_flow_control(host)

    async def connect(self, auto_adjust_comm_params: bool = True, device : Optional['PiezoDeviceBase'] = None):
        """
        Establishes a connection to a Lantronix device.

        This asynchronous method attempts to connect to a Lantronix device using
        either the provided MAC address or by discovering devices on the network.

        - If self.host is None and self.MAC is provided, it discovers the
          device's IP address using the MAC address.
        - If both self.host and self.MAC are None, it discovers all available
          Lantronix devices on the network and selects the first one.

        Once the device's IP address is determined, it establishes a Telnet
        connection to the device using the specified host and port.

        Raises:
            RuntimeError: If no devices are found during discovery.
        """
        if not self.__host and self.__MAC:
            self.__host = await xport.discover_lantronix_device_async(self.__MAC)
            if not self.__host:
                raise RuntimeError(f"Device with MAC address {self.__MAC} not found")
        elif not self.__host and not self.__MAC:
            devices = await xport.discover_lantronix_devices_async()
            if not devices:
                raise RuntimeError("No devices found")
            self.__host = devices[0].ip
            self.__MAC = devices[0].mac

        try:
            # ensure that flow control XON and XOFF chars are forwarded to host
            if auto_adjust_comm_params:
                logger.debug("Adjusting communication parameters for device %s", self.__host)
                await TelnetProtocol.configure_flow_control_mode(self.__host)
                logger.debug("Communication parameters adjusted for device %s", self.__host)

            logger.debug("Connecting to device %s", self.__host)
            await self.__connect_telnetlib()
            logger.debug("Connected to device %s", self.__host)
        except asyncio.TimeoutError as exc:
            raise RuntimeError(f"Device with host address {self.__host} not found") from exc


    async def flush_input(self):
        """
        Discard all available input within a short timeout window.
        """
        try:
            while True:
                data = await asyncio.wait_for(self.__reader.read(1024), 0.01)
                if not data:
                    break
        except asyncio.TimeoutError:
            pass  # expected when no more data arrives within timeout       


    async def write(self, cmd: str):
        await self.flush_input()
        self.__writer.write(cmd)


    async def read_until(self, expected: bytes = TransportProtocol.XON, timeout : float = TransportProtocol.DEFAULT_TIMEOUT_SECS) -> str:
        data = await asyncio.wait_for(self.__reader.readuntil(expected), timeout)
        return data.decode('utf-8').strip("\x11\x13") # strip XON and XOFF characters
        

    async def close(self):
        if self.__writer:
            self.__writer.close()
            self.__writer = None
            self.__reader.close()
            self.__reader = None

    @property
    def host(self) -> str:
        """
        Returns the host address.
        """
        return self.__host
    
    @property
    def MAC(self) -> str:
        """
        Returns the MAC address.
        """
        return self.__MAC
    
    @classmethod
    async def discover_devices(cls, flags: DiscoverFlags)  -> List[DetectedDevice]:
        """
        Asynchronously discovers all devices connected via ethernet interface

        Returns:
            list: A list of dictionaries containing device information (IP and MAC addresses).
        """
        network_endpoints = await xport.discover_lantronix_devices_async()
    
        async def detect_on_endpoint(network_endpoint: NetworkEndpoint) -> DetectedDevice | None:
            logger.debug("Connecting to network endpoint: %s", network_endpoint)
            protocol = TelnetProtocol(host=network_endpoint.ip)
            try:
                detected_device = DetectedDevice(
                    transport=TransportType.TELNET,
                    identifier=network_endpoint.ip,
                    mac=network_endpoint.mac
                )
                    
                return detected_device
            except Exception as e:
                # We do ignore the exception - if it is not possible to connect to the device, we just return None
                print(f"Error for network endpoint {network_endpoint}: {e.__class__.__name__} {e}")
                return None
            finally:
                await protocol.close()

        # Run all detections concurrently
        tasks = [detect_on_endpoint(endpoint) for endpoint in network_endpoints]
        results = await asyncio.gather(*tasks)

        # Filter out Nones
        return [dev for dev in results if dev]


    def get_info(self) -> TransportProtocolInfo:
        """
        Returns metadata about the transport protocol, such as type and identifier.
        """
        return TransportProtocolInfo(
            transport=TransportType.TELNET,
            identifier=self.__host,
            mac=self.__MAC
        )