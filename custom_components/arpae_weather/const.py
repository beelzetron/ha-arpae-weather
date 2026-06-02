"""Constants for the ARPAE Weather integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "arpae_weather"

CONF_PROVINCE = "province"
CONF_ZONE = "zone"
CONF_ALERT_ZONE = "alert_zone"

DEFAULT_PROVINCE = "BO"
DEFAULT_ZONE = "P"
DEFAULT_ALERT_ZONE = "C2"
DEFAULT_SCAN_INTERVAL = timedelta(hours=2)

VALID_PROVINCES = ("BO", "MO", "PR", "RE", "PC", "FE", "RA", "FC", "RN")
VALID_ZONES = ("P", "C", "R")

ATTR_COLOR = "color"
ATTR_DESCRIPTION = "description"
ATTR_ENDS_AT = "ends_at"
ATTR_LINK = "link"
ATTR_PHENOMENA = "phenomena"
ATTR_STARTS_AT = "starts_at"
ATTR_TITLE = "title"
ATTR_VALIDITA = "validita"
ATTR_ZONE = "zone"
