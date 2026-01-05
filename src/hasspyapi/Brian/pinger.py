import subprocess

def is_bulb_online(ip_address):
    """
    Returns True if the device is online, False if offline.
    Designed for Linux systems (Home Assistant OS, Ubuntu, Debian, etc).
    """
    command = ['ping', '-c', '1', '-W', '1', ip_address]
    
    if ip_address == "192.168.1.200":
        print("Starting ping")
    # Run the ping command, suppressing output
    response = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    if ip_address == "192.168.1.200":
        print("Ping finished: " + str(response.returncode == 0))
    return response.returncode == 0