from time import sleep, time_ns
from threading import Thread
import traceback
import asyncio

from .hass_websocket_layer import HassWebSocketLayer

class HassEventListener:
    def __init__(self, ws_url, ws_headers):
        '''
        Creates a websocket subscribed to events, and defines decorators which call functions on recieving certain events
        '''
        self.ws_url = ws_url
        self.ws_headers = ws_headers

        # A list of tuples of functions (conditions_met, event)
        # During listening, if an event matches conditions_met, the event is called
        self.events = []

        # Save the last time conditions were not met for each function
        # If an event is fired due to duration, last_false is set to None until condition_met fails
        self.last_false = []

        # Save the required duration for each event to be fired
        self.duration = []

    def trigger_when(self, conditions_met, duration=None):
        '''
        A function decorator which will save a set of conditions and event to be called when conditions are met
        If duration (seconds), then the event is fired when conditions are met for duration seconds (just once)

        conditions_met should return:
            true if conditions are met
            false if conditions are not met
            None if the event is not valid for the event (for instance, the event doesnt match the right device, or if the event exists but we arent listening to a device)
        '''
        def decorator(event):
            self.events.append((conditions_met, event))
            self.last_false.append(time_ns()) # Assume the last false is now
            self.duration.append(duration)
            return event

        return decorator
    
    def _fire_events(self, msg):
        '''
        Fire off all events if conditions are met
        Also handle duration checks
        '''
        for i, (conditions_met, event) in enumerate(self.events):
            c_met = False
            ignore_c_met = False # ignore c_met if duration is not long enough, or if duration is too long (event already fired)

            # Call in try-except to avoid conditions_met from breaking the loop
            try:
                c_met = conditions_met(msg)
            except:
                print(traceback.format_exc())

            if c_met and self.duration[i] and not self.last_false[i]:
                # Event has fired already due to duration and has not yet been false yet
                ignore_c_met = True

            elif c_met and self.duration[i]:
                # This has a duration and a last_false (so it can still be triggered)

                # check if duration has passed
                if time_ns() - self.last_false[i] > self.duration[i] * 1e9:
                    # Enough time has passed. Set last_false to None since it should no longer be triggered
                    self.last_false[i] = None
                else:
                    # Not enough time has passed
                    ignore_c_met = True

            if c_met and not ignore_c_met:
                # Conditions are met and we do not ignore, so we fire event
                try:
                    event(msg)
                except:
                    print(traceback.format_exc())
            elif c_met is not None and not ignore_c_met:
                # conditions are not met, it is valid, and we should not ignore it, so we reset time
                self.last_false[i] = time_ns()

    async def _listen(self):
        '''
        Private helper function which subscribes a websocket and recieves event messages
        '''
        async with await HassWebSocketLayer.authorize(self.ws_url, self.ws_headers) as ws:
            await ws.subscribe()
            
            while True:
                msg = await ws.recv()

                if msg.get("type") == "event" and msg.get("event").get("event_type") == "state_changed":
                    msg = msg.get("event").get("data")

                    self._fire_events(msg)

    def _periodically_check(self, interval):
        '''
        Every interval seconds, fire all events with None as parameter
        '''
        while True:
            self._fire_events(None)

            sleep(interval)

    def start(self, interval=5):
        '''
        Call functions marked by trigger_when when conditions_met passes on events from hass, and every `interval` seconds
        '''
        Thread(target=asyncio.run, args=(self._listen(),)).start()
        Thread(target=self._periodically_check, args=(interval,)).start()