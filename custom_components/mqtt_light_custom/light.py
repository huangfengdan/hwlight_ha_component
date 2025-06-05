import logging
import json
import voluptuous as vol

from homeassistant.core import callback 
from homeassistant.components import mqtt
from homeassistant.components.light import (
    LightEntity,
    PLATFORM_SCHEMA,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
)
from homeassistant.const import CONF_NAME, STATE_ON, STATE_OFF
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "MQTT Light"
DEFAULT_QOS = 0

CONF_COMMAND_TOPIC = "command_topic"
CONF_STATE_TOPIC = "state_topic"
CONF_BRIGHTNESS_COMMAND_TOPIC = "brightness_command_topic"
CONF_BRIGHTNESS_STATE_TOPIC = "brightness_state_topic"
CONF_RGB_COMMAND_TOPIC = "rgb_command_topic"
CONF_RGB_STATE_TOPIC = "rgb_state_topic"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_COMMAND_TOPIC): mqtt.valid_publish_topic,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_STATE_TOPIC): mqtt.valid_subscribe_topic,
        vol.Optional(CONF_BRIGHTNESS_COMMAND_TOPIC): mqtt.valid_publish_topic,
        vol.Optional(CONF_BRIGHTNESS_STATE_TOPIC): mqtt.valid_subscribe_topic,
        vol.Optional(CONF_RGB_COMMAND_TOPIC): mqtt.valid_publish_topic,
        vol.Optional(CONF_RGB_STATE_TOPIC): mqtt.valid_subscribe_topic,
    }
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up MQTT light."""
    name = config.get(CONF_NAME)
    command_topic = config.get(CONF_COMMAND_TOPIC)
    state_topic = config.get(CONF_STATE_TOPIC)
    brightness_command_topic = config.get(CONF_BRIGHTNESS_COMMAND_TOPIC)
    brightness_state_topic = config.get(CONF_BRIGHTNESS_STATE_TOPIC)
    rgb_command_topic = config.get(CONF_RGB_COMMAND_TOPIC)
    rgb_state_topic = config.get(CONF_RGB_STATE_TOPIC)

    async_add_entities(
        [
            MQTTLight(
                name,
                command_topic,
                state_topic,
                brightness_command_topic,
                brightness_state_topic,
                rgb_command_topic,
                rgb_state_topic,
            )
        ]
    )

class MQTTLight(LightEntity):
    """Representation of an MQTT light."""

    def __init__(
        self,
        name,
        command_topic,
        state_topic,
        brightness_command_topic,
        brightness_state_topic,
        rgb_command_topic,
        rgb_state_topic
    ):
        """Initialize MQTT light."""
        self._name = name
        self._state = False
        self._brightness = None
        self._rgb_color = None
        self._command_topic = command_topic
        self._state_topic = state_topic
        self._brightness_command_topic = brightness_command_topic
        self._brightness_state_topic = brightness_state_topic
        self._rgb_command_topic = rgb_command_topic
        self._rgb_state_topic = rgb_state_topic
        self._unique_id = f"mqtt_light_xxx"

    async def async_added_to_hass(self):
        """Subscribe to MQTT topics."""
        @callback
        def state_message_received(msg):
            """Handle new MQTT state messages."""
            payload = msg.payload
            if payload == "ON":
                self._state = True
            elif payload == "OFF":
                self._state = False
            self.async_write_ha_state()

        @callback
        def brightness_message_received(msg):
            """Handle new MQTT brightness messages."""
            self._brightness = int(msg.payload)
            self.async_write_ha_state()

        @callback
        def rgb_message_received(msg):
            """Handle new MQTT RGB messages."""
            rgb = json.loads(msg.payload)
            self._rgb_color = (rgb["r"], rgb["g"], rgb["b"])
            self.async_write_ha_state()

        if self._state_topic is not None:
            await mqtt.async_subscribe(
                self.hass, self._state_topic, state_message_received, 1
            )
        if self._brightness_state_topic is not None:
            await mqtt.async_subscribe(
                self.hass, self._brightness_state_topic, brightness_message_received, 1
            )
        if self._rgb_state_topic is not None:
            await mqtt.async_subscribe(
                self.hass, self._rgb_state_topic, rgb_message_received, 1
            )

    @property
    def unique_id(self):
        """返回唯一标识符"""
        return self._unique_id
    
    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        return self._brightness

    @property
    def rgb_color(self):
        """Return the RGB color value."""
        return self._rgb_color

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    @property
    def supported_features(self):
        """Flag supported features."""
        features = 0
        if self._brightness_command_topic is not None:
            features = features | SUPPORT_BRIGHTNESS
        if self._rgb_command_topic is not None:
            features = features | SUPPORT_COLOR
        return features

    async def async_turn_on(self, **kwargs):
        """Turn the device on."""
        await mqtt.async_publish(
            self.hass, self._command_topic, "ON", 1, False
        )
        self._state = True
        
        if ATTR_BRIGHTNESS in kwargs and self._brightness_command_topic is not None:
            brightness = kwargs[ATTR_BRIGHTNESS]
            await mqtt.async_publish(
                self.hass, self._brightness_command_topic, brightness, 1, False
            )
            self._brightness = brightness
            
        if ATTR_RGB_COLOR in kwargs and self._rgb_command_topic is not None:
            rgb = kwargs[ATTR_RGB_COLOR]
            rgb_dict = {"r": rgb[0], "g": rgb[1], "b": rgb[2]}
            await mqtt.async_publish(
                self.hass, self._rgb_command_topic, json.dumps(rgb_dict), 1, False
            )
            self._rgb_color = rgb

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the device off."""
        await mqtt.async_publish(
            self.hass, self._command_topic, "OFF", 1, False
        )
        self._state = False
        self.async_write_ha_state()