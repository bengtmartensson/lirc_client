"""Stuff common for IR remotes."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import logging
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
from .const import (
    POWER_FALLBACKS,
    POWER_OFF_SYNONYMS,
    POWER_ON_SYNONYMS,
)
_LOGGER = logging.getLogger(__name__)

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

    def __init__(self, hardware, ip, name, count, on_command, off_command):
        self._hardware = hardware
        self._unique_id = __name__ + base64.b64encode((ip + name).encode('utf-8')).decode('us-ascii')
        self._power = False
        self._name = name
        self._count = count
        self._on_command = on_command
        self._off_command = off_command

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self._name
    
    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        return self._unique_id

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
            count = self._count * num_repeats
            _LOGGER.info("Sending command '%s' to remote '%s', count=%d", cmd, self._name, count)
            self._hardware.send(cmd, count)
