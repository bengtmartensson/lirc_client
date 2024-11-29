"""Stuff common for IR remotes."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import base64

from homeassistant.components import remote
from homeassistant.components.remote import (
    ATTR_NUM_REPEATS,
    DEFAULT_NUM_REPEATS,
    PLATFORM_SCHEMA as REMOTE_PLATFORM_SCHEMA,
)

from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

CONF_COMMANDS   = "commands"
CONF_DATA       = "data"
CONF_IR_COUNT   = "ir_count"
CONF_MODADDR    = "modaddr"
CONF_CONNADDR   = "connaddr"

POWER_ON_SYNONYMS = [ "power_on", "power on", "on" ]
POWER_FALLBACKS = [ "power_toggle", "power toggle", "power", "key_power" ]                
POWER_OFF_SYNONYMS = [ "power_off", "power off" "off", "standby" ]

def on_command(commands) -> str:
    return find_command_fallback(commands, POWER_ON_SYNONYMS, POWER_FALLBACKS)

def off_command(commands) -> str:
    return find_command_fallback(commands, POWER_OFF_SYNONYMS, POWER_FALLBACKS)

def find_command_fallback(commands, synonyms, fallbacks) -> str:
    return find_command(commands, synonyms) or find_command(commands, fallbacks)
 
def find_command(commands, vocabulary) -> str:
    for cmd in commands:
        if cmd in vocabulary:
            return cmd
        if cmd.upper() in vocabulary:
            return cmd.upper()
    return None


class AbstractRemote(remote.RemoteEntity):
    """Abstract super class for device that sends commands to a remote."""

    def __init__(self, hardware, ip, name, count, commands):
        self._hardware = hardware
        self._ip = ip
        self._power = False
        self._name = name
        self._count = count
        self._on_command = on_command(commands)
        self._off_command = off_command(commands)

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self._name
    
    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        return __name__ + base64.b64encode((self._ip + self._name).encode('utf-8')).decode('us-ascii')

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._power

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        self.send_command([ self._on_command ], ATTR_NUM_REPEATS=self._count)
        self._power = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        self.send_command([ self._off_command ], ATTR_NUM_REPEATS=self._count)
        self._power = False
        self.schedule_update_ha_state()

    def send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send a command to one device."""
        num_repeats = kwargs.get(ATTR_NUM_REPEATS, DEFAULT_NUM_REPEATS)
        for cmd in command:
            self._hardware.send(cmd, self._count * num_repeats)
