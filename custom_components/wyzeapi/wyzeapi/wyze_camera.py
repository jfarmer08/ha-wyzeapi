import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class WyzeCamera():
    def __init__(self, api, device_mac, friendly_name, state, onoffstate, ssid, ip, device_model):
        _LOGGER.debug("Camera " + friendly_name + " "+ ip + " " + "initializing.")

        self._api = api
        self._device_mac = device_mac
        self._friendly_name = friendly_name
        self._state = state
        self._avaliable = True
        self._just_changed_state = False
        self._device_model = device_model
        self._ssid = ssid
        self._ip = ip
        self._onoffstate = onoffstate
        self._rtsp_port = '554'

    async def async_turn_on(self):
        _LOGGER.debug("Camera Switch " + self._friendly_name + " turning on.")
        url = 'https://api.wyzecam.com/app/v2/auto/run_action'

        payload = {
            'phone_id': self._api._device_id,
            'action_params': {},
            'provider_key': self._device_model,
            'app_name': 'com.hualai.WyzeCam',
            'app_version': '2.6.62',
            'action_key': 'power_on',
            ' ': '',
            'sc':'01dd431d098546f9baf5233724fa2ee2',
            'sv':'22bd9023a23b4b0b9977e4297ca100dd',
            'phone_system_type': '1',
            'app_ver': 'com.hualai.WyzeCam___2.6.62',
            'ts': '1575948896791',
            'instance_id': self._device_mac,
            'access_token': self._api._access_token
        }

        loop = asyncio.get_running_loop()
        loop.create_task(self._api.async_do_request(url, payload))

        self._state = True
        self._just_changed_state = True
    
    async def async_turn_off(self):
        _LOGGER.debug("Camera Switch " + self._friendly_name + " turning off.")
        url = 'https://api.wyzecam.com/app/v2/auto/run_action'

        payload = {
            'phone_id': self._api._device_id,
            'action_params': {},
            'provider_key': self._device_model,
            'app_name': 'com.hualai.WyzeCam',
            'app_version': '2.6.62',
            'action_key': 'power_off',
            ' ': '',
            'sc':'01dd431d098546f9baf5233724fa2ee2',
            'sv':'22bd9023a23b4b0b9977e4297ca100dd',
            'phone_system_type': '1',
            'app_ver': 'com.hualai.WyzeCam___2.6.62',
            'ts': '1575948896791',
            'instance_id': self._device_mac,
            'access_token': self._api._access_token
        }

        loop = asyncio.get_running_loop()
        loop.create_task(self._api.async_do_request(url, payload))

        self._state = False
        self._just_changed_state = True

    def is_on(self):
        return self._onoffstate

    async def async_update(self):
        _LOGGER.debug("Camera Switch " + self._friendly_name + " updating.")
        if self._just_changed_state == True:
            self._just_changed_state == False
        else:
            url = "https://api.wyzecam.com/app/v2/device/get_property_list"

            payload = {
                "target_pid_list":[],
                "phone_id": self._api._device_id,
                "device_model": self._device_model,
                "app_name":"com.hualai.WyzeCam",
                "app_version":"2.6.62",
                "sc":"01dd431d098546f9baf5233724fa2ee2",
                "sv":"22bd9023a23b4b0b9977e4297ca100dd",
                "device_mac": self._device_mac,
                "app_ver":"com.hualai.WyzeCam___2.6.62",
                "phone_system_type":"1",
                "ts":"1575955054511",
                "access_token": self._api._access_token
            }

            data = await self._api.async_do_request(url, payload)

            for item in data['data']['property_list']:
                if item['pid'] == "P3":
                    self._state = True if int(item['value']) == 1 else False
                elif item['pid'] == "P5":
                    self._avaliable = False if int(item['value']) == 0 else True
