import logging

from ..hass_scripts import start_scripts, script
logger = logging.getLogger(__name__)

class Outside:
    def __init__(self, home, listener):
        self.listener = listener

        self.brian_tracker = home.please().filter(name = "*my pog*", type = "device_tracker").get()
        self.meaghan_tracker = home.please().filter(entity_id = "*meaghans_iphone", type = "device_tracker").get()

        self.living_room_lights = home.please().filter(area = "Living Room", type = "light")
        self.main_room_fan = home.please().filter(area = "Living Room", type = "fan").get()
        self.kitchen_lights = home.please().filter(area = "Kitchen", type = "light")
        self.projector = home.please().filter(area = "Living Room", name = "Android TV").get()

        self.bedroom_lights = home.please().filter(area = "Bedroom", type = "light")
        self.bedroom_fan = home.please().filter(area = "Bedroom", type = "fan").get()
        self.bathroom_lights = home.please().filter(area = "Bathroom", type = "light")

        self.gate = home.please().filter(area = "Parking Lot", type = "switch").get()

        self.default_light_settings = {"color_temp_kelvin": 2500, "brightness": 255}

        start_scripts(self)

    @script
    def save_power(self):
        '''
        Turn off all lights and devices when both phones are out of the house
        '''

        def both_phones_went_out(event):
            if not self.brian_tracker.matches(event) and not self.meaghan_tracker.matches(event):
                return None
            
            brian_is_home = self.brian_tracker.get_state() == "home"
            meaghan_is_home = self.meaghan_tracker.get_state() == "home"

            if brian_is_home or meaghan_is_home:
                return False
            
            someone_left = event.get("new_state").get("state") == "not_home" \
                       and event.get("old_state").get("state") == "home"

            return someone_left
        
        @self.listener.trigger_when(both_phones_went_out)
        def power_off_home(event):
            logger.info("Turning off all home lights, everyone is gone")
            self.living_room_lights.turn_off()
            self.main_room_fan.turn_off()
            self.kitchen_lights.turn_off()
            self.projector.turn_off()

            self.bedroom_lights.turn_off()
            self.bedroom_fan.turn_off()
            self.bathroom_lights.turn_off()

    @script
    def coming_home(self):
        '''
        Turn on the main room lights when a home owner comes in
        Also open the gate
        '''
        def a_phone_went_in(event):
            if not self.brian_tracker.matches(event) and not self.meaghan_tracker.matches(event):
                return None
            
            someone_got_home = event.get("new_state").get("state") == "home" \
                           and event.get("old_state").get("state") == "not_home"

            return someone_got_home
        
        @self.listener.trigger_when(a_phone_went_in)
        def power_on_main_room(event):
            logger.info("Turning on main room lights, someone is home")
            self.living_room_lights.turn_on(**self.default_light_settings)
            self.kitchen_lights.turn_on(**self.default_light_settings)
