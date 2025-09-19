# HassPyAPI

This is a small repo I use for [Home Assistant](https://www.home-assistant.io/) scripts in my home. It functions as a user-friendly layer between the [Home Assistant REST API](https://developers.home-assistant.io/docs/api/rest/) and Python, which attempts to decrease reliance on the `entity_id` attribute.

I personally prefer writing code to using the built-in Home Assistant automation/script builder. However, the [Home Assistant REST API](https://developers.home-assistant.io/docs/api/rest/) and [web socket API](https://developers.home-assistant.io/docs/api/websocket/) both heavily rely on the `entity_id` attribute to function. Since Home Assistant supports a vast selection of add-ons and services, the corresponding `entity_id`s can often be not user-friendly, and be difficult to determine.

For instance, I use [Phillips Hue](https://www.philips-hue.com/en-us) lights in my home. The [Home Assistant Phillipe Hue service](https://www.home-assistant.io/integrations/hue/) serves as a wonderful layer between my Hue lights and the Home Assistant interface. However, automated `entity_id` fields are chosen very haphazardly. For instance, a desk light in my bedroom of the name "Desk Light" was given the `entity_id`, `light.desk_light`, whereas a desk light in my wife's study room of the name "Desk Light" was given the `entity_id`, `light.study_room_desk_light`. 

To fix this, I created this (very small) layer between Python and the Home Assistant API, which uses services from the REST API and web socket API, in order to control Home Assistant through the primary use of the `friendly_name` attribute, `area_name` attribute, and device type. Below is an example of the code I use to turn off my kitchen lights using this library.

```
home = Home("HOME ASSISTANT IP", "HOME ASSISTANT KEY")

home.please().filter(area = "Kitchen", type = "light").turn_off()
```

In order to build scripts, this library also comes with a `trigger_when` function decorator, and a `script` function decorator, which can be used to build scripts. For instance, below is a simple example of a script which toggles my bedroom ceiling fan when I press a button on my Phillips Hue dimmer switch.

```
from ..hass_scripts import start_scripts, script

class BedRoom:
    def __init__(self, home, listener):
        self.listener = listener

        self.bedroom = home.please().filter(area = "Bedroom")

        self.fan_button = bedroom.filter(name = "*Button 4*")
        self.fan = bedroom.filter(type = "fan")

        start_scripts(self)

    @script
    def fan_switch(self):
        '''
        Toggle the fan when the fourth button is pressed
        '''
        def fan_button_pressed(event):
            if not self.fan_button.matches(event):
                return
            
            return event.get("new_state").get("attributes").get("event_type") == "initial_press"
        
        @self.listener.trigger_when(fan_button_pressed)
        def toggle_fan(event):
            self.fan.toggle()

if __name__ == "__main__":
    home = Home("HOME ASSISTANT IP", "HOME ASSISTANT KEY")

    listener = home.listener()
    listener.start()

    Bedroom(home, listener)
```

For more examples, please see the examples branch, which contains all of the scripts I use to control my own home. Enjoy!