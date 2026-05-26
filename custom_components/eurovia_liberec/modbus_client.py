"""Modbus TCP client for PLC communication."""
import logging
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

_LOGGER = logging.getLogger(__name__)


class ModbusClient:
    """Modbus TCP client wrapper."""

    def __init__(self, host: str, port: int = 502, slave_id: int = 1):
        """Initialize Modbus client."""
        self.host = host
        self.port = port
        self.slave_id = slave_id
        self.client = ModbusTcpClient(host=host, port=port)
        self.connect()

    def connect(self) -> bool:
        """Connect to Modbus server."""
        try:
            if not self.client.connect():
                _LOGGER.error(f"Failed to connect to {self.host}:{self.port}")
                return False
            _LOGGER.info(f"Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            _LOGGER.error(f"Connection error: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Modbus server."""
        if self.client:
            self.client.close()

    def read_register(self, address: int) -> int or None:
        """Read single holding register."""
        try:
            result = self.client.read_holding_registers(
                address=address, count=1, slave=self.slave_id
            )
            if result.isError():
                _LOGGER.error(f"Error reading register {address}")
                return None
            return result.registers[0]
        except Exception as e:
            _LOGGER.error(f"Error reading register {address}: {e}")
            return None

    def read_registers(self, address: int, count: int) -> list or None:
        """Read multiple holding registers."""
        try:
            result = self.client.read_holding_registers(
                address=address, count=count, slave=self.slave_id
            )
            if result.isError():
                _LOGGER.error(f"Error reading registers {address}-{address+count-1}")
                return None
            return result.registers
        except Exception as e:
            _LOGGER.error(
                f"Error reading registers {address}-{address+count-1}: {e}"
            )
            return None

    def write_register(self, address: int, value: int) -> bool:
        """Write single holding register."""
        try:
            result = self.client.write_register(
                address=address, value=value, slave=self.slave_id
            )
            if result.isError():
                _LOGGER.error(f"Error writing register {address}")
                return False
            _LOGGER.debug(f"Wrote register {address}: {value}")
            return True
        except Exception as e:
            _LOGGER.error(f"Error writing register {address}: {e}")
            return False
