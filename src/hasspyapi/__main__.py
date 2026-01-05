from .home import Home

if __name__ == "__main__":
    import logging
    import sys

    # Set the base logging level for everything
    logging.basicConfig(
        level=logging.INFO,  # change to DEBUG if you want very verbose logs
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("hass.log"),       # file output
            logging.StreamHandler(sys.stdout)      # console output
        ]
    )

    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    home = Home("localhost:8123", open("hass_key", "r").read())
    print("Home initialized")

    listener = home.listener()
    listener.start(interval=1)

    from .Brian.bed_room import BedRoom
    bedroom = BedRoom(home, listener)

    import traceback
    print("Console has started")
    while True:
        st = input()
        try:
            exec(st)
        except:
            traceback.print_exc()