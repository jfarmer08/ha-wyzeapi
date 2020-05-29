"""Define support for Wyze Camera cameras"""
import asyncio
import logging
import hashlib
from random import SystemRandom
from enum import Enum

from .wyzeapi.wyzeapi import WyzeApi
from . import DOMAIN


from haffmpeg.camera import CameraMjpeg
from haffmpeg.tools import ImageFrame, IMAGE_JPEG

from homeassistant.components.camera import SUPPORT_ON_OFF, SUPPORT_STREAM, Camera
from homeassistant.components.ffmpeg import DATA_FFMPEG
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.aiohttp_client import async_aiohttp_proxy_stream


_LOGGER = logging.getLogger(__name__)

ATTR_HARDWARE_VERSION = "hardware_version"
ATTR_SERIAL = "serial_number"
ATTR_SOFTWARE_VERSION = "software_version"

DEFAULT_ATTRIBUTION = "Data provided by Wyze"
DEFAULT_FFMPEG_ARGUMENTS = " -vcodec copy -maxFPS 30"
DEFAULT_FFMPEG_ARGUMENTS_IMAGE = "-vframes 1"

_RND = SystemRandom()

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Wyze camera platform."""
    _LOGGER.debug("""Creating new WyzeApi camera component""")
    async_add_entities(WyzeCamera(hass, camera) for camera in await hass.data[DOMAIN]["wyzeapi_account"].async_list_camera())


class WyzeCamera(Camera):
    """Define a Wyze Camera."""

    def __init__(self, hass, camera):
        """Initialize."""
        super().__init__()

        self._async_unsub_dispatcher_connect = None
        self._camera = camera
        self._name = camera._friendly_name
        self._state = camera._state
        self._ssid = camera._ssid
        self._local_ip = camera._ip
        self._ssid = camera._ssid
        self._device_mac = camera._device_mac
        self._device_model = camera._device_model
        self._rtsp_port = camera._rtsp_port
        self._username = "admin"
        self._password = "admin"
        self.is_streaming = False
        self._rtsp_port = camera._rtsp_port
        self._ffmpeg = hass.data[DATA_FFMPEG]
        self._ffmpeg_arguments = DEFAULT_FFMPEG_ARGUMENTS
        self._ffmpeg_arguments_image = DEFAULT_FFMPEG_ARGUMENTS_IMAGE
        self._ffmpeg_image_frame = ImageFrame(self._ffmpeg.binary, loop=hass.loop)
        self._ffmpeg_stream = CameraMjpeg(self._ffmpeg.binary, loop=hass.loop)
        self._last_image = None
        self._last_image_url = None
        self._stream_url = f"rtsp://{self._username}:{self._password}@{self._local_ip}:554/live"
        self.access_tokens = self.update_tokens()
        self._local_rtsp_port = 554

    def update_tokens(self):
        """Update the used token."""
        token = hashlib.sha256(_RND.getrandbits(256).to_bytes(32, "little")).hexdigest()
        return token

    @property
    def brand(self):
        """Return the camera brand."""
        return "Wyze"

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attributes = {
            ATTR_ATTRIBUTION: DEFAULT_ATTRIBUTION,
            ATTR_HARDWARE_VERSION: self._device_model,
            ATTR_SERIAL: self._device_mac,
            ATTR_SOFTWARE_VERSION: "1.0.0",
            "access_token": self.access_tokens,
        }
        return attributes

    @property
    def model(self):
        """Return the name of this camera."""
        return self._device_model

    @property
    def name(self):
        """Return the name of this camera."""
        return self._name

    @property
    def should_poll(self):
        """Return False, updates are controlled via the hub."""
        return False

    @property
    def supported_features(self):
        """Return supported features."""
        return SUPPORT_ON_OFF | SUPPORT_STREAM

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._device_mac

    async def async_camera_image(self):
        """Return a frame from the camera stream."""
        self._last_image = await asyncio.shield(self._ffmpeg_image_frame.get_image(self._stream_url, output_format=IMAGE_JPEG,extra_cmd=self._ffmpeg_arguments_image,)
        )
        _LOGGER.debug("Camera %s source image: %s", self._device_mac, self._stream_url)
        return self._last_image

    async def async_disable_motion_detection(self):
        """Disable doorbell's motion detection"""

    async def async_enable_motion_detection(self):
        """Enable doorbell's motion detection"""

    async def async_turn_off(self):
        await self._camera.async_turn_off()

    async def async_turn_on(self):
        """Turn on the RTSP stream."""
        await self._camera.async_turn_on()

    async def stream_source(self):
        """Return the stream source."""
        if self._local_rtsp_port:
            rtsp_stream_source = (
                f"rtsp://{self._username}:{self._password}@"
                f"{self._local_ip}:{self._local_rtsp_port}/live"
            )
            _LOGGER.debug("Camera %s source stream: %s", self._device_mac, rtsp_stream_source)
            self._rtsp_stream = rtsp_stream_source
            self.is_streaming = True
            return rtsp_stream_source
        return None


    async def handle_async_mjpeg_stream(self, request):
        """Generate an HTTP MJPEG stream from the camera."""
        #if not self._stream_url:
        #return await self.async_camera_image()

        await self._ffmpeg_stream.open_camera(self._stream_url, extra_cmd=self._ffmpeg_arguments)

        try:
            stream_reader = await self._ffmpeg_stream.get_reader()
            _LOGGER.debug("Camera %s mjpg stream: %s", self._device_mac, rtsp_stream_source)
            return await async_aiohttp_proxy_stream(self.hass,request,stream_reader,self._ffmpeg.ffmpeg_stream_content_type,)
        finally:
            await self._ffmpeg_stream.close()