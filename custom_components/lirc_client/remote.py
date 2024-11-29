"""Support for sending command to a TCP Lirc server using Lirconian."""

from __future__ import annotations

from collections.abc import Iterable
import logging
from typing import Any
from .abstract_remote import (
    AbstractRemote,
    CONF_MODADDR,
    CONF_CONNADDR,
    CONF_COMMANDS,
    CONF_DATA,
    CONF_IR_COUNT
)

import lirconian
import voluptuous as vol

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
DEFAULT_TIMEOUT = 2000
DEFAULT_IR_COUNT = 1

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
                    vol.Optional(CONF_IR_COUNT): cv.positive_int,
                    vol.Required(CONF_COMMANDS): vol.All(
                        cv.ensure_list,
                        [
                            {
                                vol.Required(CONF_NAME): cv.string,
                                vol.Optional(CONF_IR_COUNT): cv.positive_int,
                                vol.Optional(CONF_DATA): cv.string, # for compatibility, ignored
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
        count = int(data.get(CONF_IR_COUNT, DEFAULT_IR_COUNT))
        commands = []
        for cmd in data.get(CONF_COMMANDS):
            commands.append(cmd[CONF_NAME].strip())
        devices.append(LirconianRemote(lrc, config[CONF_HOST], name, count, commands))
    add_entities(devices, True)


class LirconianRemote(AbstractRemote):
    """Device that sends commands to an Lirconian device."""

    def __init__(self, lirconian, ip, name, count, commands):
        super().__init__(lirconian, ip, name, count, commands)

    def send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send a command to one device."""
        num_repeats = kwargs.get(ATTR_NUM_REPEATS, DEFAULT_NUM_REPEATS)
        for cmd in command:
            self._hardware.send_ir_command(self._name, cmd, self._count * num_repeats)
