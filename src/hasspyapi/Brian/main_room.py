import logging

from ..hass_scripts import start_scripts, script
logger = logging.getLogger(__name__)

class MainRoom:
    def __init__(self, home, listener):
        self.listener = listener

        kitchen = home.please().filter(area = "Kitchen")
        living_room = home.please().filter(area = "Living Room")

        self.sensor_motion = kitchen.filter(name = "*Sensor Motion*").get()
        self.main_room_power_button = living_room.filter(name = "*Button 1*").get()
        self.main_room_fan_button = living_room.filter(name = "*Button 4*").get()
    
        self.kitchen_lights = kitchen.filter(type = "light")
        self.living_room_lights = living_room.filter(type = "light")

        self.fan = living_room.filter(type = "fan").get()

        self.projector = living_room.filter(name = "Android TV").get()

        # Save whether or not to supress motion. When projector is on, motion should be supressed
        self.supress_motion = False

        self.default_light_settings = {"color_temp_kelvin": 2500, "brightness": 255}

        start_scripts(self)

    def lights_are_bright(self):
        '''
        Return whether or not the lights are in their fully bright state
        Note, sum > 1 is used since one light does not store kelvins or brightness
        '''
        attributes = self.kitchen_lights.get_attributes()
        kelvins_mismatch = [attribute.get("color_temp_kelvin") != self.default_light_settings["color_temp_kelvin"] for attribute in attributes]
        brightnesses_mismatch = [attribute.get("brightness") != self.default_light_settings["brightness"] for attribute in attributes]
        if sum(kelvins_mismatch) > 1 or sum(brightnesses_mismatch) > 1:
            return False
        
        attributes = self.living_room_lights.get_attributes()
        kelvins_mismatch = [attribute.get("color_temp_kelvin") != self.default_light_settings["color_temp_kelvin"] for attribute in attributes]
        brightnesses_mismatch = [attribute.get("brightness") != self.default_light_settings["brightness"] for attribute in attributes]
        if sum(kelvins_mismatch) > 1 or sum(brightnesses_mismatch) > 1:
            return False
        
        return True

    @script
    def save_power(self):
        '''
        Turn off all lights when there is no motion for 15 minutes
        '''
        def no_motion(event):
            if event:
                # This case in not event driven
                return None
            
            if self.supress_motion:
                return False
            
            return self.sensor_motion.get_state() == 'off'
        
        # Turn off lights after 15 seconds
        @self.listener.trigger_when(no_motion, duration = 15 * 60)
        def power_off_lights(event):
            logger.info("Saving power in the living room")
            self.kitchen_lights.turn_off()
            self.living_room_lights.turn_off()

    @script
    def motion_sensor(self):
        '''
        Make lights nice and bright once motion starts!
        Only set lights to bright if all lights are off
        '''
        def motion_started(event):
            if not self.sensor_motion.matches(event):
                # This event belongs a different device
                return None
            
            if self.supress_motion:
                return False
            
            return event.get("new_state").get("state") == "on" \
               and event.get("old_state").get("state") == "off" \
               and all([state in {"off", "unavailable"} for state in self.kitchen_lights.get_state()]) \
               and all([state in {"off", "unavailable"} for state in self.living_room_lights.get_state()])
        
        # Turn on lights when motion is started
        @self.listener.trigger_when(motion_started)
        def power_on_lights(event):
            logger.info("Turning on living room lights due to motion")
            self.kitchen_lights.turn_on(**self.default_light_settings)
            self.living_room_lights.turn_on(**self.default_light_settings)

    @script
    def light_switch(self):
        '''
        Let the top button of the light switch toggle the lights
        If the lights are in any intermediate state or off, switch turns them on
        If the lights are on, turn them off
        '''

        def power_button_pressed(event):
            if not self.main_room_power_button.matches(event):
                # Event must belong to main_room_power_button
                return None
            
            return event.get("new_state").get("event_type") == "initial_press"
        
        @self.listener.trigger_when(power_button_pressed)
        def toggle_lights(event):
            if self.lights_are_bright():
                # Turn off
                logger.info("Turning off lights from the light switch")
                self.kitchen_lights.turn_off()
                self.living_room_lights.turn_off()
            else:
                # Turn on
                logger.info("Turning on lights from the light switch")
                self.kitchen_lights.turn_on(**self.default_light_settings)
                self.living_room_lights.turn_on(**self.default_light_settings)

    @script
    def fan_switch(self):
        '''
        Toggle the fan when the fourth button is pressed
        '''
        def fan_button_pressed(event):
            if not self.main_room_fan_button.matches(event):
                # Event must belong to main_room_fan_button
                return None
            
            return event.get("new_state").get("event_type") == "initial_press"
        
        @self.listener.trigger_when(fan_button_pressed)
        def toggle_fan(event):
            logger.info("Toggling the fan from the light switch")
            self.fan.toggle()

    @script
    def projector_mode(self):
        '''
        Turn on and off projector mode when projector turns on or off
        This turns off lights when projector is on, on when it is off
        Also supresses motion
        '''

        def projector_mode_changed(event):
            if not self.projector.matches(event):
                return None
            
            return event.get("new_state").get("state") != event.get("old_state").get("state")
        
        @self.listener.trigger_when(projector_mode_changed)
        def toggle_projector_mode(event):
            if event.get("new_state").get("state") == "on":
                # projector turned on
                logger.info("Enabling projector mode")
                self.supress_motion = True
                self.kitchen_lights.turn_off()
                self.living_room_lights.turn_off()
            else:
                # projector turned off
                logger.info("Disabling projector mode")
                self.supress_motion = False
                self.kitchen_lights.turn_on(**self.default_light_settings)
                self.living_room_lights.turn_on(**self.default_light_settings)