"""The Eurovia Liberec Modbus PLC integration."""
import asyncio
import logging
from datetime import datetime, timedelta

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .modbus_client import ModbusClient
from .modbus_db import ModbusDatabase

_LOGGER = logging.getLogger(__name__)

DOMAIN = "eurovia_liberec"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST, default="192.168.1.100"): str,
                vol.Required(CONF_PORT, default=502): int,
                vol.Optional("slave_id", default=1): int,
                vol.Optional("scan_interval", default=60): int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Eurovia Liberec component."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    host = conf.get(CONF_HOST)
    port = conf.get(CONF_PORT)
    slave_id = conf.get("slave_id", 1)
    scan_interval = conf.get("scan_interval", 60)

    hass.data[DOMAIN] = {
        "client": ModbusClient(host, port, slave_id),
        "db": ModbusDatabase("/config/eurovia_db.sqlite"),
        "scan_interval": scan_interval,
    }

    # Initialize database
    hass.data[DOMAIN]["db"].init_db()

    # Start the polling task
    hass.loop.create_task(
        async_update_data(
            hass,
            hass.data[DOMAIN]["client"],
            hass.data[DOMAIN]["db"],
            scan_interval,
        )
    )

    return True


async def async_update_data(
    hass: HomeAssistant, client: ModbusClient, db: ModbusDatabase, interval: int
) -> None:
    """Update data from Modbus PLC."""
    last_position = -1

    while True:
        try:
            # Read current position from PLC (register 25)
            plc_position = client.read_register(25)

            # If position changed, read all data
            if plc_position != last_position:
                # Read registers 35-37 (time and date)
                time_data = client.read_registers(35, 3)
                if time_data:
                    hours = (time_data[0] >> 8) & 0xFF
                    minutes = time_data[0] & 0xFF
                    day = (time_data[1] >> 8) & 0xFF
                    month = time_data[1] & 0xFF
                    year = time_data[2]

                    # Read temperature registers (27-34)
                    temps = client.read_registers(27, 8)
                    if temps:
                        # Convert temperatures (divide by 10)
                        temp_values = [t / 10.0 for t in temps]

                        # Read other registers (10-25)
                        others = client.read_registers(10, 16)

                        # Create timestamp
                        try:
                            timestamp = datetime(
                                year, month, day, hours, minutes, 0
                            )
                        except ValueError:
                            timestamp = datetime.now()

                        # Store in database
                        db.insert_measurement(
                            timestamp=timestamp,
                            temperatures=temp_values,
                            others=others if others else [0] * 16,
                        )

                        _LOGGER.info(
                            f"Data stored: {timestamp} - Temps: {temp_values}"
                        )

                        last_position = plc_position

                        # Update register 500 with current position
                        client.write_register(500, plc_position)

            await asyncio.sleep(interval)

        except Exception as e:
            _LOGGER.error(f"Error updating data: {e}")
            await asyncio.sleep(interval)
