import subprocess

def is_bulb_online(ip_address):
    """
    Returns True if the device is online, False if offline.
    Designed for Linux systems (Home Assistant OS, Ubuntu, Debian, etc).
    """
    command = ['ping', '-c', '1', '-W', '1', ip_address]
    
    # Run the ping command, suppressing output
    response = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    return response.returncode == 0