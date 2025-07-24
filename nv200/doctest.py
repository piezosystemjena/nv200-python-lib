import asyncio

from nv200.shared_types import TransportType
from nv200.connection_utils import connect_to_single_device
from nv200.nv200_device import NV200Device
from PySide6.QtCore import QStandardPaths


async def main():
    print("Home:", QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation))
    print("Temp:", QStandardPaths.writableLocation(QStandardPaths.StandardLocation.TempLocation))
    print("AppData:", QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    print("Documents:", QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation))

if __name__ == "__main__":
    asyncio.run(main())
