import json
import serial
from threading import Thread

from .HandGestures.hand import FingerTips, Hand
from .HandGestures.status_handle import StatusHandle
    
class HandListener:
    def __init__(self, listener, seconds):
        '''
        Fire events to the listener on detection of certain hand signals
        The hand tolerance must last for given seconds
        '''
        USB_PORT = '/dev/ttyUSB0'

        self.ser = serial.Serial(
            port=USB_PORT,
            baudrate=9600,
            timeout=1
        )

        self.listener = listener
        self.seconds = seconds

        self.handle = StatusHandle()

        Thread(target=self.read_from_usb).start()

    def read_from_usb(self):
        '''
        Read hand data from USB and fire event on hand detection
        '''
        while True:
            if self.ser.in_waiting > 0:
                msg = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if msg:
                    hands_fingers = json.loads(msg)

                    hands = []

                    for hand_fingers in hands_fingers:
                        hand_fingers.append(None)
                        hands.append(Hand(*hand_fingers))

                    hand_events = []

                    # For now, we will just consider one hand.
                    if len(hands) == 1:
                        hand = hands[0]

                        if all(hand.fingers):
                            hand_events.append("ALL_FINGERS")

                        if hand.only(FingerTips.INDEX):
                            hand_events.append("1")

                        if hand.only(FingerTips.INDEX, FingerTips.MIDDLE):
                            hand_events.append("2")

                        if hand.only(FingerTips.INDEX, FingerTips.MIDDLE, FingerTips.RING):
                            hand_events.append("3")

                        if hand.only(FingerTips.INDEX, FingerTips.MIDDLE, FingerTips.RING, FingerTips.PINKY):
                            hand_events.append("4")

                    print(hand_events)

                    self.handle.update(hand_events)

                    events_to_fire = self.handle.all_true_for(self.seconds)

                    for event_to_fire in events_to_fire:
                        event = {}
                        event["entity_id"] = "hand.bedroom"
                        event["msg"] = event_to_fire

                        self.listener.fire_event(event)