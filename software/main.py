from boardsupport.frankenstein_controller import FrankensteinController
import time
import logging, sys

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
for handler in logging.getLogger().handlers:
    handler.setFormatter(logging.Formatter("[%(levelname)s]:%(name)s:%(message)s"))


controller = FrankensteinController()
controller.reset()

controller.button4_led["blink"] = True
controller.button1_led["blink"] = True
controller.button4_led["value"] = True
controller.button1_led["value"] = True
controller.display2["blink"] = True
controller.display3["blink"] = True
controller.display1["value"] = 0
