from boardsupport.frankenstein_controller import FrankensteinRotaryController
import time
import logging, sys
import micropython
import network
import json
import webrepl

# Set up logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
for handler in logging.getLogger().handlers:
    handler.setFormatter(logging.Formatter("[%(levelname)s]:%(name)s:%(message)s"))

# Exception buffer for interrupt exceptions et al
micropython.alloc_emergency_exception_buf(100)

if __name__ == "__main__":
    # Set up the board
    controller = FrankensteinRotaryController()
    controller.reset()

    # Enable WIFI and WebREPL
    config_file = open("config.json")
    config = json.load(config_file)

    wlan = network.WLAN(network.STA_IF)
    network.hostname("rotary")
    wlan.active(True)
    wlan.connect(config['ssid'], config['wlanpw'])
    #webrepl.start(password=config['webrepl_pw'])

