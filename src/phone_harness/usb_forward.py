"""USB port forwarding restricted to this computer."""
import asyncio
import sys

from pymobiledevice3.tcp_forwarder import UsbmuxTcpForwarder

if __name__ == "__main__":
    local, remote = map(int, sys.argv[1:3])
    serial = sys.argv[3] if len(sys.argv) > 3 else None
    asyncio.run(UsbmuxTcpForwarder(serial, remote, local).start(address="127.0.0.1"))
