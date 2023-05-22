from boardsupport.frankenstein_controller import FrankensteinRotaryController
import time
import logging, sys

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
for handler in logging.getLogger().handlers:
    handler.setFormatter(logging.Formatter("[%(levelname)s]:%(name)s:%(message)s"))


controller = FrankensteinRotaryController()
controller.reset()


#from machine import Pin
#from time import sleep_us, sleep_ms

#en_pin = Pin(8, Pin.OUT)
#en_pin.value(0)
#step_pin = Pin(9, Pin.OUT)
#dir_pin = Pin(10, Pin.OUT)


#def step():
#    i = 0
#    while i < 200*16:
#        step_pin.toggle()
#        sleep_us(100)
#        i = i+1
