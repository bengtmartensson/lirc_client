"""Support for sending command to a Global Cache."""

from __future__ import annotations
from .abstract_remote import (
    AbstractRemote,
    on_command,
    off_command,
    CONF_MODADDR,
    CONF_CONNADDR,
    CONF_COMMANDS,
    CONF_DATA,
    CONF_IR_COUNT,
    CONF_ON_COMMAND,
    CONF_OFF_COMMAND,
)
import logging

import pyglobalcache
import voluptuous as vol

#from homeassistant.components import remote
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
#    DEVICE_DEFAULT_NAME,
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
                                vol.Optional(CONF_IR_COUNT, default=DEFAULT_IR_COUNT): cv.positive_int,
                                vol.Optional(CONF_ON_COMMAND, default=False): cv.boolean,
                                vol.Optional(CONF_OFF_COMMAND, default=False): cv.boolean,   
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
        found_on_command = None
        found_off_command = None
        commands = {}
        for cmd in data.get(CONF_COMMANDS):
            cmdname = cmd[CONF_NAME].strip()
            cmddata = cmd[CONF_DATA].strip()
            if cmd[CONF_ON_COMMAND]:
                found_on_command = cmdname
            if cmd[CONF_OFF_COMMAND]:
                found_off_command = cmdname
            commands[cmdname] = pyglobalcache.GCIRDevice.Command(cmddata)
        if found_on_command is None:
            found_on_command = on_command(commands)
        if found_off_command is None:
            found_off_command = off_command(commands)
        devices.append(GlobalCacheRemote(globalCache, config[CONF_HOST], name, module, connaddr,
                                          count, commands, found_on_command, found_off_command))
    add_entities(devices, True)


class GlobalCacheRemote(AbstractRemote):
    """Device that sends commands to a GlobalCache device."""

    def __init__(self, globalCache, ip, name, module, connaddr, count, commands, on_command, off_command):
        super().__init__(pyglobalcache.GCIRDevice(globalCache, module, connaddr, commands),
                                ip, name, count, on_command, off_command)
        _LOGGER.info('Setting up GlobalCache Remote on IP "%s" with name "%s" on="%s" off="%s"', ip, name, on_command, off_command)
