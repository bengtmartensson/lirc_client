"""Constants for the lirc_client integration."""

CONF_COMMANDS       = "commands"
CONF_CONNADDR       = "connaddr"
CONF_DATA           = "data"
CONF_IR_COUNT       = "ir_count"
CONF_MODADDR        = "modaddr"
CONF_OFF_COMMAND    = "off_command"
CONF_ON_COMMAND     = "on_command"
DEFAULT_CONNADDR    = 1
DEFAULT_IR_COUNT    = 1
DEFAULT_PORT        = 8765
DEFAULT_TIMEOUT     = 2000
DOMAIN              = "lirc_client"
POWER_ON_SYNONYMS   = [ "power_on", "power on", "on" ]
POWER_FALLBACKS     = [ "power_toggle", "power toggle", "power", "key_power" ]
POWER_OFF_SYNONYMS  = [ "power_off", "power off" "off", "standby" ]
