from .hass_api_layer import HassApiLayer

class HassCommand:
    def __init__(self, url, api_key, devices):
        '''
        A pretty command builder and executor for home assistant API commands
        '''

        self.url = url
        self.api_key = api_key

        # A list of json objects corresponding to devices
        self.devices = devices

        self.api_layer = HassApiLayer(url, api_key)

    def filter(self, **kwargs):
        '''
        Create a HassCommand object whose devices only match attributes specified in **kwargs

        ex. HassCommand().filter(area_id = area_id) returns a HassCommand object whose devices are all in area area_id.

        For kwarg values that start/end with *, they are treated like the Kleene star (match anything)
        '''

        # Persist a new list of devices
        devices = []
        for device in self.devices:
            for kwarg in kwargs:
                if not device[kwarg]:
                    # Device doesnt have the kwarg, so it cannot match
                    break

                if kwargs[kwarg].startswith("*") and kwargs[kwarg].endswith("*"):
                    if kwargs[kwarg][1:-1] not in device[kwarg]:
                        # kwargs[kwarg] not contained in device[kwarg]
                        break

                elif kwargs[kwarg].startswith("*"):
                    if not device[kwarg].endswith(kwargs[kwarg][1:]):
                        # device[kwarg] does not end with kwargs[kwarg]
                        break

                elif kwargs[kwarg].endswith("*"):
                    if not device[kwarg].startswith(kwargs[kwarg][:-1]):
                        # device[kwarg] does not start with kwargs[kwarg]
                        break
                    
                elif device[kwarg] != kwargs[kwarg]:
                    # This is a nonmatch
                    break
            else:
                # All kwargs match (loop not broken), this is a match
                devices.append(device)

        return HassCommand(self.url, self.api_key, devices)
    
    def get(self):
        '''
        Attempt to return a HassCommand containing just one device. 
        If there is not just one device, raise an error
        '''
        if len(self.devices) != 1:
            raise RuntimeError(f"Cannot get single device from {len(self.devices)} devices")
        else:
            return self
        
    def matches(self, event):
        '''
        Return whether or not the devices match the entity_id in the given event.
        Helpful for shorthand in scripts
        '''
        for device in self.devices:
            match = event and event.get("entity_id") == device.get("entity_id")

            if not match:
                return False
            
        return True
    
    def _refine(self, lst):
        '''
        Given a list lst, return just its first index if its length is 1
        '''
        if len(lst) == 1:
            return lst[0]
        else:
            return lst
    
    def get_attributes(self):
        '''
        Get a list of attributes for each device
        If there is just one device, return the first element of such a list
        '''
        result = []
        for device in self.devices:
            result.append(self.api_layer.states(device["entity_id"])["attributes"])

        return self._refine(result)
        
    def get_state(self):
        '''
        Return a list of states for each device
        If there is just one device, return the first element of such a list
        '''
        result = []
        for device in self.devices:
            result.append(self.api_layer.states(device["entity_id"])["state"])
        
        return self._refine(result)
    
    def turn_on(self, **attributes):
        '''
        Set attributes for all devices via given attributes, and turn devices on
        Return list of responses
        If there is just one device, return the first element of such a list
        '''
        result = []
        for device in self.devices:
            result.append(self.api_layer.turn_on(device["entity_id"], device["type"], **attributes))

        return self._refine(result)
    
    def set_attributes(self, **attributes):
        '''
        Set attributes for all devices that are ON via given attributes
        Devices that are not on do not turn on, or change attributes
        Return list of responses
        If there is just one device, return the first element of such a list
        '''
        # Get device states. We only change attributes if device is on
        states = self.get_state()

        result = []
        for state, device in zip(states, self.devices):
            if state == "on":
                result.append(self.api_layer.turn_on(device["entity_id"], device["type"], **attributes))
            else:
                result.append({"state": "off"})

        return self._refine(result)
    
    def turn_off(self):
        '''
        Turn off all devices
        Return list of responses
        If there is just one device, return the first element of such a list
        '''
        result = []
        for device in self.devices:
            result.append(self.api_layer.turn_off(device["entity_id"], device["device"]))

        return self._refine(result)
    
    def toggle(self, **attributes):
        '''
        Toggle all devices and set attributes
        Return list of responses
        If there is just one device, return the first element of such a list
        '''
        result = []
        for device in self.devices:
            result.append(self.api_layer.toggle(device["entity_id"], device["device"], **attributes))

        return self._refine(result)