import asyncio

from .hass_command import HassCommand
from .hass_event_listener import HassEventListener
from .hass_websocket_layer import HassWebSocketLayer

class Home:
    def __init__(self, url, api_key):
        '''
        Initializes the API via url and api_key on HomeAssistant server
        Builds internal dictionary of devices
        '''

        self.url = url
        self.api_key = api_key

        self.ws_url = f"ws://{url}/api/websocket"
        self.ws_headers = {
            "type": "auth",
            "access_token": api_key
        }

        self.devices = self._get_devices()

    def please(self):
        '''
        Return a corresponding HassCommand object
        '''
        return HassCommand(self.url, self.api_key, self.devices)
    
    def listener(self):
        '''
        Return a corresponding HassEventListener object
        '''
        return HassEventListener(self.ws_url, self.ws_headers)

    def _strip_area_prefix(self, friendly_name, area_name):
        '''
        Remove leading area_name prefix from given friendly_name
        ex. friendly_name = Kitchen Ceiling Light, area_name = Kitchen --> Ceiling Light
        
        * HomeAssistant likes to sometimes add the room name before the friendly name, which makes it much more difficult to handle the API using friendly names.
        '''
        if friendly_name.startswith(area_name):
            return friendly_name[len(area_name):].strip()
        else:
            return friendly_name
        
    async def _get_ws_data(self):
        '''
        Connect to hass via websocket to get area/device/entity registries.
        areas: Contains area names and their area_ids
        devices: Contains devices (friendly names) and their area_ids, along with (useless) device_id
        entities: Contains device_ids and their (useful) entity_ids

        NOTE: entities DO have area_id, but they are often all null
        '''

        async with await HassWebSocketLayer.authorize(self.ws_url, self.ws_headers) as ws:
            areas = await ws.call("config/area_registry/list", 1)
            devices = await ws.call("config/device_registry/list", 2)
            entities = await ws.call("config/entity_registry/list", 3)

            return areas, devices, entities
    
    def _build_devices(self, areas, devices, entities):
        '''
        Build a list of {entity_id, name, area, area_id, type} for each device
        '''
        # Map of area_ids to area names
        area_map = {area["area_id"]: area.get("name", "Unknown") for area in areas}

        # Map of device_ids to device entries
        device_map = {device["id"]: device for device in devices}

        # Map of area names to device dictionaries
        result = []
        for ent in entities:
            # Ignore hidden/dummy entities
            if ent.get("entity_category") == 'config':
                continue
            if ent.get("hidden_by") is not None:
                continue
            if ent.get("disabled_by") is not None:
                continue

            entity_id = ent.get("entity_id")
            
            device_id = ent.get("device_id")
            device = device_map.get(device_id)

            if device and device.get("model") == "Room":
                # Do not include rooms, since they will duplicate devices in calls
                continue
            
            if device:
                area_id = device.get("area_id")
            else:
                # Device does not exist, fall back to area_id from entity
                area_id = ent.get("area_id")

            area_name = area_map.get(area_id)

            # Now the one issue is the device display name
            # Selection is listed in order of preference
            # 1. The user changed the name manually in hass (saved in "name")
            # 2. There is an existing friendly name (saved in "original_name")

            display_name = ent.get("name") or ent.get("original_name")

            if display_name and "DEPRECATED" in display_name:
                # Some names contain "DEPRECATED" instead of being null. Override to original_name (friendly name) instead
                display_name = ent.get("original_name")

            if display_name and area_name:
                # Make sure display name does not have room name prefix
                display_name = self._strip_area_prefix(display_name, area_name)

            # Determine device type via entity_id naming conventions
            device_type = None
            if "." in entity_id:
                device_type = entity_id.split(".")[0]

            # Push this device to results
            result.append({"entity_id": entity_id,
                           "name": display_name,
                           "area_id": area_id,
                           "area": area_name,
                           "type": device_type
                           })

        return result
    
    def _get_devices(self):
        areas, devices, entities = asyncio.run(self._get_ws_data())
        return self._build_devices(areas, devices, entities)