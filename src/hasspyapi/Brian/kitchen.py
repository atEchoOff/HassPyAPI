import logging
from .pinger import is_bulb_online

from ..hass_scripts import start_scripts, script
logger = logging.getLogger(__name__)

class Kitchen:
    def __init__(self, home, listener):
        self.listener = listener

        self.main_ceiling_light_ip = "192.168.1.206"
        self.living_room_ceiling_light_ip = "192.168.1.203"

        self.lights = home.please().filter(area="Kitchen", type="light", name="!Ceiling")
        self.all_lights = home.please().filter(area="Kitchen", type="light")
        self.living_room_lights = home.please().filter(area="Living Room", type="light", name="!Ceiling")
        self.all_living_room_lights = home.please().filter(area="Living Room", type="light")

        self.default_light_settings = {"color_temp_kelvin": 3000, "brightness": 255}

        self.switch1 = home.please().filter(name="Main Room Button 1").get()
        self.switch2 = home.please().filter(name="Main Room Button 2").get()
        self.switch3 = home.please().filter(name="Main Room Button 3").get()
        self.switch4 = home.please().filter(name="Main Room Button 4").get()

        start_scripts(self)

    def all_lights_off(self, lights):
        '''
        Return whether or not the lights are in their fully bright state
        Note, sum > 1 is used since one light does not store kelvins or brightness
        '''
        attributes = lights.get_attributes(if_available=True)
        brightnesses_mismatch = [attribute.get("brightness") is not None and attribute.get("brightness") > 0 for attribute in attributes]
        if sum(brightnesses_mismatch) >= 1:
            return False
        else:
            return True

    @script
    def switch_toggle_lights(self):
        '''
        Toggle all lights when button 1 is pressed
        '''
        def button_1_pressed(event):
            if not self.switch1.matches(event):
                return None
            
            return event.get("new_state").get("event_type") == "initial_press"
        
        @self.listener.trigger_when(button_1_pressed)
        def toggle_all_lights(event):
            if not self.all_lights_off(self.all_lights) or not self.all_lights_off(self.all_living_room_lights):
                # Turn off
                self.all_living_room_lights.turn_off(if_available=True)
                self.all_lights.turn_off(if_available=True)
            else:
                # Turn on
                self.all_living_room_lights.turn_on(if_available=True, **self.default_light_settings)
                self.all_lights.turn_on(if_available=True, **self.default_light_settings)


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
            logger.info("Detected ceiling light, turning on kitchen")

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
            self.lights.turn_off()
            logger.info("Lost connection from ceiling light, turning off kitchen")