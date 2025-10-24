import logging
import datetime
from .bed_room_hand_listener import HandListener

from ..hass_scripts import start_scripts, script
logger = logging.getLogger(__name__)

class BedRoom:
    def __init__(self, home, listener):
        self.listener = listener

        bedroom = home.please().filter(area = "Bedroom")

        self.sensor_motion = bedroom.filter(name = "*Sensor Motion*").get()

        self.power_button = bedroom.filter(name = "*Button 1*").get()
        self.fan_button = bedroom.filter(name = "*Button 4*").get()

        self.closet_power_button = home.please().filter(area = "Closet", name = "*Button 1*").get()
        self.closet_light = home.please().filter(area = "Closet", type = "light").get()
    
        self.lights = bedroom.filter(type = "light")

        self.fan = bedroom.filter(type = "fan").get()

        self.temperature = bedroom.filter(name = "*Sensor Temperature*").get()
        
        self.google_assistant = home.please().google_assistant

        # Save whether or not to supress motion. When asleep, do not turn on lights from motion!
        self.supress_motion = False

        self.default_light_settings = {"color_temp_kelvin": 2500, "brightness": 255}

        HandListener(listener, 1)

        start_scripts(self)

    def lights_are_bright(self):
        '''
        Return whether or not the lights are in their fully bright state
        Note, sum > 1 is used since one light does not store kelvins or brightness
        '''
        attributes = self.lights.get_attributes()
        kelvins_mismatch = [attribute.get("color_temp_kelvin") != self.default_light_settings["color_temp_kelvin"] for attribute in attributes]
        brightnesses_mismatch = [attribute.get("brightness") != self.default_light_settings["brightness"] for attribute in attributes]
        if sum(kelvins_mismatch) > 1 or sum(brightnesses_mismatch) > 1:
            return False
        else:
            return True
        
    @script
    def show_hands(self):
        '''
        Just print something when hands are detected in the bedroom
        '''
        def hand_message(event):
            print(event)
            if not event:
                # This is not event driven
                return None
            
            if event.get("entity_id") != "hand.bedroom":
                # This event belongs a different device
                return None
            return True
        
        # Turn off lights after 15 seconds
        @self.listener.trigger_when(hand_message)
        def power_off_lights(event):
            logger.info("Found a hand: " + event.get("msg"))

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
            logger.info("Saving bedroom power")
            self.lights.turn_off()

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
               and all([state in {"off", "unavailable"} for state in self.lights.get_state()])
        
        # Turn on lights when motion is started
        @self.listener.trigger_when(motion_started)
        def power_on_lights(event):
            logger.info("Powering on lights due to motion")
            self.lights.turn_on(**self.default_light_settings)

    @script
    def light_switch(self):
        '''
        Let the top button of the light switch toggle the lights
        If the lights are in any intermediate state or off, switch turns them on
        If the lights are on, turn them off
        '''

        def power_button_pressed(event):
            if not self.power_button.matches(event):
                return None
            
            return event.get("new_state").get("event_type") == "initial_press"
        
        @self.listener.trigger_when(power_button_pressed)
        def toggle_lights(event):
            if self.lights_are_bright():
                # Turn off
                logger.info("Turning off lights from light switch")
                self.lights.turn_off()
                self.supress_motion = True
            else:
                # Turn on
                logger.info("Turning on lights from light switch")
                self.lights.turn_on(**self.default_light_settings)
                self.supress_motion = False

    @script
    def fan_switch(self):
        '''
        Toggle the fan when the fourth button is pressed
        '''
        def fan_button_pressed(event):
            if not self.fan_button.matches(event):
                # Event must belong to main_room_fan_button
                return None
            
            return event.get("new_state").get("event_type") == "initial_press"
        
        @self.listener.trigger_when(fan_button_pressed)
        def toggle_fan(event):
            logger.info("Toggling fan from light switch")
            self.fan.toggle()

    @script
    def night_temperature(self):
        '''
        Ensure the bedroom temperature stays between 72 and 74
        '''
        def temperature_below_72(event):
            if event:
                return None
            
            start_time = datetime.time(20, 30) # 8:30 pm
            end_time = datetime.time(8, 30) # 8:30 am
            curtime = datetime.datetime.now().time()

            night_time = start_time < curtime or curtime < end_time
            
            if not night_time:
                # We are not asleep
                return False
            
            print(f"Current bedroom temperature: {self.temperature.get_state()}")
            return float(self.temperature.get_state()) < 72

        @self.listener.trigger_when(temperature_below_72, duration = 60)
        def raise_temperature(event):
            logger.info("Raising the temperature in the bedroom to 80")
            self.google_assistant("Set the thermostat to 80 degrees")

        def temperature_above_74(event):
            if event:
                return None
            
            start_time = datetime.time(20, 30) # 8:30 pm
            end_time = datetime.time(8, 30) # 8:30 am
            curtime = datetime.datetime.now().time()

            night_time = start_time < curtime or curtime < end_time
            
            if not night_time:
                # We are not asleep
                return False
            
            return float(self.temperature.get_state()) > 74
        
        @self.listener.trigger_when(temperature_above_74, duration = 60)
        def lower_temperature(event):
            logger.info("Lowering the temperature in the bedroom to 65")
            self.google_assistant("Set the thermostat to 65 degrees")

    @script
    def day_temperature(self):
        '''
        Reset the temperature back to 76 during the day, at 8:45 am
        '''

        def it_is_after_845_before_9(event):
            if event:
                return None
            
            start_time = datetime.time(8, 45) # 8:45 am
            end_time = datetime.time(9, 0) # 9:00 am
            curtime = datetime.datetime.now().time()

            return start_time < curtime < end_time
        
        @self.listener.trigger_when(it_is_after_845_before_9, duration = 30)
        def reset_temperature(event):
            logger.info("Resetting the temperature to 76")
            self.google_assistant("Set the thermostat to 76 degrees")

    @script
    def closet_light_switch(self):
        '''
        Let the top button of the light switch toggle the lights of the closet
        If the lights are in any intermediate state or off, switch turns them on
        If the lights are on, turn them off
        '''

        def power_button_pressed(event):
            if not self.closet_power_button.matches(event):
                return None
            
            return event.get("new_state").get("event_type") == "initial_press"
        
        @self.listener.trigger_when(power_button_pressed)
        def toggle_lights(event):
            logger.info("Toggling closet light from light switch")
            self.closet_light.toggle()