"""Support for switches using GlobalCache using relays."""

from __future__ import annotations
from typing import Any
import voluptuous as vol
import pyglobalcache
import base64

from homeassistant.components.switch import (
    PLATFORM_SCHEMA as SWITCH_PLATFORM_SCHEMA,
    SwitchEntity,
)

from homeassistant.const import (
    CONF_DEVICES,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_TIMEOUT,
#    DEVICE_DEFAULT_NAME,
)
from .const import (
    CONF_MODADDR,
    CONF_CONNADDR,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

CONF_RELAYS = 'relays'
DEFAULT_MODADDR = 3 # Different from the IR sends

PLATFORM_SCHEMA = SWITCH_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        vol.Optional(CONF_MODADDR, default=DEFAULT_MODADDR) : cv.positive_int,
        vol.Required(CONF_RELAYS): vol.All (
            cv.ensure_list,
            [
                {
                    vol.Optional(CONF_NAME): cv.string,
                    vol.Optional(CONF_CONNADDR): cv.positive_int
                }
            ]
        )
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    globalcache = pyglobalcache.GlobalCache(
        config[CONF_HOST], int(config[CONF_PORT]),
        int(config[CONF_TIMEOUT])
    )
    module = int(config[CONF_MODADDR])
    switches = []
    for relay in config[CONF_RELAYS]:
        name = relay[CONF_NAME]
        conn = relay[CONF_CONNADDR]
        switches.append(GlobalCacheRelay(globalcache, config[CONF_HOST], name, module, conn))
    add_entities(switches, True)


class GlobalCacheRelay(SwitchEntity):
    """Represent a switch/relay from GlobalCache."""

    def __init__(self, globalcache, ip, name, module, conn):
        self._relaydevice = pyglobalcache.GCRelayDevice(globalcache, module, conn)
        self._name = name
        self._state = None
        self._unique_id = __name__ + base64.b64encode((ip + str(module) + str(conn)).encode('utf-8')).decode('us-ascii')

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return the state of the entity."""
        return self._state

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        return self._unique_id

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        self._relaydevice.turn_on()
        self._state = True

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        self._relaydevice.turn_off()
        self._state = False

    def update(self) -> None:
        """Update the sensor state."""
        self._state = self._relaydevice.getstate()

    def set_state(self, state):
        """Set the current state."""
        self._state = not state == 0
        self.schedule_update_ha_state()
