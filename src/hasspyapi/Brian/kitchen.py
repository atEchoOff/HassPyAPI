import logging
from .pinger import is_bulb_online

from ..hass_scripts import start_scripts, script
logger = logging.getLogger(__name__)

class Kitchen:
    def __init__(self, home, listener):
        self.listener = listener

        self.main_ceiling_light_ip = "192.168.1.206"

        self.google_assistant = home.please().google_assistant

        print(home.please().filter(area="Kitchen", type="light").devices)

        start_scripts(self)

    def turn_on_bright(self):
        '''
        Set color and brightness of all lights to be bright
        '''
        self.google_assistant("Set kitchen brightness to 100%")
        self.google_assistant("Set kitchen color to warm white")

    def turn_off(self):
        '''
        Turn off all lights
        '''
        self.google_assistant("Turn off kitchen lights")

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
            self.turn_on_bright()

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
            self.turn_off()