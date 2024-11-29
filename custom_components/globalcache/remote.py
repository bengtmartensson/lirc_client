"""Support for sending command to a TCP Lirc server using Lirconian."""

from __future__ import annotations

from collections.abc import Iterable
import logging
from typing import Any

import pyglobalcache
import voluptuous as vol
import base64
#from . import const

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

DOMAIN = "globalcache"

DEFAULT_PORT = 4998
DEFAULT_TIMEOUT = 5000
DEFAULT_IR_COUNT = 1
DEFAULT_MODADDR = 1
DEFAULT_CONNADDR = 1

CONF_MODADDR = "modaddr"
CONF_CONNADDR = "connaddr"
CONF_COMMANDS = "commands"
CONF_DATA = "data"
CONF_IR_COUNT = "ir_count"

POWER_ON = "power_on"
POWER_OFF = "power_off"

PLATFORM_SCHEMA = REMOTE_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        vol.Optional(CONF_MODADDR, default=DEFAULT_MODADDR) : cv.positive_int,
        vol.Optional(CONF_CONNADDR, default=DEFAULT_CONNADDR) : cv.positive_int,
        vol.Required(CONF_DEVICES): vol.All(
            cv.ensure_list,
            [
                {
                    vol.Optional(CONF_NAME): cv.string,
                    vol.Optional(CONF_MODADDR): cv.positive_int,
                    vol.Optional(CONF_CONNADDR): cv.positive_int,
                    vol.Optional(CONF_IR_COUNT): cv.positive_int,
                    vol.Required(CONF_COMMANDS): vol.All(
                        cv.ensure_list,
                        [
                            {
                                vol.Required(CONF_NAME): cv.string,
                                vol.Optional(CONF_IR_COUNT): cv.positive_int,
                                vol.Required(CONF_DATA): cv.string
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
    """Set up the GlobalCache connection."""
    globalCache = pyglobalcache.GlobalCache(
        config[CONF_HOST], int(config[CONF_PORT]),
        int(config[CONF_TIMEOUT])
    )
    default_module = int(config[CONF_MODADDR])
    default_connaddr = int(config[CONF_CONNADDR])

    devices = []
    for data in config[CONF_DEVICES]:
        name = data.get(CONF_NAME)
        count = int(data.get(CONF_IR_COUNT, DEFAULT_IR_COUNT))
        module = int(data.get(CONF_MODADDR, default_module))
        connaddr = int(data.get(CONF_CONNADDR, default_connaddr))
        commands = {}
        for cmd in data.get(CONF_COMMANDS):
            cmdname = cmd[CONF_NAME].strip()
            if not cmdname:
                cmdname = '""'
            cmddata = cmd[CONF_DATA].strip()
            if not cmddata:
                cmddata = '""'
            commands[cmdname] = pyglobalcache.GCIRDevice.Command(cmddata)
        devices.append(GlobalCacheRemote(globalCache, config[CONF_HOST], name, module, connaddr, count, commands))
    add_entities(devices, True)


class GlobalCacheRemote(remote.RemoteEntity):
    """Device that sends commands to a GlobalCache device."""

    def __init__(self, globalCache, ip, name, module, connaddr, count, commands):
        """Initialize device."""
        self._device = pyglobalcache.GCIRDevice(globalCache, module, connaddr, commands )
        self._ip = ip
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
        return 'globalcache_' + base64.b64encode((self._ip + self._name).encode('utf-8')).decode('us-ascii')

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
        for cmd in command:
            self._device.send(cmd, self._count * num_repeats)
