"""Support for sending command to a TCP Lirc server using Lirconian."""

from __future__ import annotations

from collections.abc import Iterable
import logging
from typing import Any

import lirconian
import voluptuous as vol

from homeassistant.components import remote
from homeassistant.components.remote import (
    ATTR_NUM_REPEATS,
    DEFAULT_NUM_REPEATS,
    PLATFORM_SCHEMA as REMOTE_PLATFORM_SCHEMA,
)
from homeassistant.const import (
    CONF_DEVICES,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_TIMEOUT,
    DEVICE_DEFAULT_NAME,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = 8765
DEFAULT_TIMEOUT = 5000
DEFAULT_COUNT = 1

CONF_COMMANDS = "commands"
CONF_DATA = "data"
CONF_COUNT = "count"

POWER_ON = "power_on"
POWER_OFF = "power_off"

PLATFORM_SCHEMA = REMOTE_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        vol.Required(CONF_DEVICES): vol.All(
            cv.ensure_list,
            [
                {
                    vol.Optional(CONF_NAME): cv.string,
                    # TODO: transmitter
                    vol.Optional(CONF_COUNT): cv.positive_int,
                    vol.Required(CONF_COMMANDS): vol.All(
                        cv.ensure_list,
                        [
                            {
                                vol.Required(CONF_NAME): cv.string,
                                vol.Optional(CONF_COUNT): cv.positive_int,
                                vol.Optional(CONF_DATA): cv.string, # ignored
                            }
                        ],
                    ),
                }
            ],
        ),
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the lirconian connection."""
    lrc = lirconian.TcpLirconian(
        config[CONF_HOST], int(config[CONF_PORT]), False, int(config[CONF_TIMEOUT])
    )

    devices = []
    for data in config[CONF_DEVICES]:
        name = data.get(CONF_NAME)
        count = int(data.get(CONF_COUNT, DEFAULT_COUNT))
        devices.append(LirconianRemote(lrc, name, count))
    add_entities(devices, True)


class LirconianRemote(remote.RemoteEntity):
    """Device that sends commands to an Lirconian device."""

    def __init__(self, lirconian, name, count):
        """Initialize device."""
        self.lirconian = lirconian
        self._power = False
        self._name = name or DEVICE_DEFAULT_NAME
        self._count = count or DEFAULT_COUNT

    @property
    def name(self):
        """Return the name of the device."""
        return self._name
    
    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        return 'lirc_client_' + self._name
    
    @property
    def is_on(self):
        """Return true if device is on."""
        return self._power

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        self._power = True
        self.send_command([ POWER_ON], ATTR_NUM_REPEATS=self._count)
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        self._power = False
        self.send_command([ POWER_OFF ], ATTR_NUM_REPEATS=self._count)
        self.schedule_update_ha_state()

    def send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send a command to one device."""
        num_repeats = kwargs.get(ATTR_NUM_REPEATS, DEFAULT_NUM_REPEATS)
        for single_command in command:
            self.lirconian.send_ir_command(self._name, single_command, self._count * num_repeats)
