import logging
from .pinger import is_bulb_online

from ..hass_scripts import start_scripts, script
logger = logging.getLogger(__name__)

class LivingRoom:
    def __init__(self, home, listener):
        self.listener = listener

        self.main_ceiling_light_ip = "192.168.1.203"

        self.lights = home.please().filter(area="Living Room", type="light")
        self.default_light_settings = {"color_temp_kelvin": 2500, "brightness": 255}
        self.off_default_light_settings = {"color_temp_kelvin": 2500, "brightness": 255}
        print(self.lights.devices)
        start_scripts(self)

    @script
    def turn_on_other_lights(self):
        '''
        Turn on other lights when main ceiling light turns on
        '''
        def main_ceiling_light_turned_on(event):
            if event:
                return None
            
            # This is a timed event. 
            # Check if IP is connected to network
            return is_bulb_online(self.main_ceiling_light_ip)

        @self.listener.trigger_when(main_ceiling_light_turned_on, duration=2)
        def doit(event):
            self.lights.turn_on(**self.default_light_settings)

    @script
    def turn_off_other_lights(self):
        '''
        Turn off other lights when main ceiling light turns on
        '''
        def main_ceiling_light_turned_off(event):
            if event:
                return None
            
            # This is a timed event. 
            # Check if IP is connected to network
            return not is_bulb_online(self.main_ceiling_light_ip)

        @self.listener.trigger_when(main_ceiling_light_turned_off, duration=2)
        def doit(event):
            self.lights.turn_on(**self.off_default_light_settings)