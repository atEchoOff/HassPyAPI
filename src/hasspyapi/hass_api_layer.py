import requests

class HassApiLayer:
    def __init__(self, url, api_key):
        '''
        A layer between the hass REST API and Python
        '''

        self.api_url = f"http://{url}/api/"
        self.api_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _get(self, endpoint):
        '''
        Safely query endpoint via hass REST API
        '''
        response = requests.get(self.api_url + endpoint, headers=self.api_headers)
        if response.status_code != 200:
            raise RuntimeError(f"There was an error with endpoint {endpoint}: {response.text}")
        
        return response.json()
    
    def _post(self, endpoint, entity_id, **data):
        '''
        Safely post data to endpoint via hass REST API
        All supported post jsons contain entity_id, so it is a required field
        '''
        data = {"entity_id": entity_id, **data}

        response = requests.post(self.api_url + endpoint, json=data, headers=self.api_headers)
        if response.status_code != 200:
            raise RuntimeError(f"There was an error posting to endpoint {endpoint}: {response.text}")
        
        return response.json()
    
    def turn_on(self, entity_id, device_type, **attributes):
        '''
        Safely access the turn_on service endpoint and pass in any available attributes (ex. hs_color, brightness etc.)
        '''
        return self._post(f"services/{device_type}/turn_on", entity_id, **attributes)
    
    def turn_off(self, entity_id, device_type):
        '''
        Safely access the turn_off service endpoint
        '''
        return self._post(f"services/{device_type}/turn_off", entity_id)
    
    def toggle(self, entity_id, device_type, **attributes):
        '''
        Safely access the toggle service endpoint and pass in any available attributes (ex. hs_color, brightness etc.)
        '''
        return self._post(f"services/{device_type}/toggle", entity_id, **attributes)
    
    def states(self, entity_id):
        '''
        Safely access the states service endpoint
        '''
        return self._get(f"states/{entity_id}")