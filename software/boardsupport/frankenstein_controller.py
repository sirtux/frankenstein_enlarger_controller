from machine import Pin, SPI, PWM, Timer
import time
import math
from .rotary_irq_rp2 import RotaryIRQ
import logging
from .debounce import DebouncedSwitch

class FrankensteinController:
    def __init__(self) -> None:
        # Logging

        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initializing FrankensteinController")
        # Setup the physical part
        self.pwm_pin = Pin(0, Pin.OUT)
        self.latch_pin = Pin(12, Pin.OUT)
        self.spi_bus = SPI(0, baudrate=10_000_000, sck=Pin(2), mosi=Pin(3))
        self.pwm = PWM(self.pwm_pin)
        self.pwm.freq(4000)
        self.pwm.duty_u16(63000)

        # Display options
        self.display1 = {"value": 1, "blink": False}
        self.display2 = {"value": 2, "blink": False}
        self.display3 = {"value": 3, "blink": False}
        self.display4 = {"value": 4, "blink": False}

        self.button1_led = {"value": False, "blink": False, "address": 8}
        self.button2_led = {"value": False, "blink": False, "address": 4}
        self.button3_led = {"value": False, "blink": False, "address": 2}
        self.button4_led = {"value": False, "blink": False, "address": 1}

        # Rotary Encoders
        self.rotary_1 = RotaryIRQ(
            pin_num_clk=6, pin_num_dt=7, min_val=0, max_val=999, half_step=True, id=1
        )
        self.rotary_2 = RotaryIRQ(
            pin_num_clk=26, pin_num_dt=1, min_val=0, max_val=999, half_step=True, id=2
        )
        self.rotary_3 = RotaryIRQ(
            pin_num_clk=19, pin_num_dt=20, min_val=0, max_val=999, half_step=True, id=3
        )
        self.rotary_4 = RotaryIRQ(
            pin_num_clk=16, pin_num_dt=17, min_val=0, max_val=999, half_step=True, id=4
        )

        self.rotary_1.add_listener(self.rotary_event)
        self.rotary_2.add_listener(self.rotary_event)
        self.rotary_3.add_listener(self.rotary_event)
        self.rotary_4.add_listener(self.rotary_event)


        # TODO: Buttons
        
        self.rotary_1_button = DebouncedSwitch(Pin(27, Pin.IN, Pin.PULL_DOWN), None)
        self.rotary_1_button.callback(self.button_event, "rotary_1_button")
        self.rotary_2_button = DebouncedSwitch(Pin(13, Pin.IN, Pin.PULL_DOWN), None)
        self.rotary_2_button.callback(self.button_event, "rotary_2_button")
        self.rotary_3_button = DebouncedSwitch(Pin(21, Pin.IN, Pin.PULL_DOWN), None)
        self.rotary_3_button.callback(self.button_event, "rotary_3_button")
        self.rotary_4_button = DebouncedSwitch(Pin(18, Pin.IN, Pin.PULL_DOWN), None)
        self.rotary_4_button.callback(self.button_event, "rotary_4_button")

        self.button1 = DebouncedSwitch(Pin(4, Pin.IN, Pin.PULL_DOWN), None)
        self.button1.callback(self.button_event, "button1")
        self.button2 = DebouncedSwitch(Pin(5, Pin.IN, Pin.PULL_DOWN), None)
        self.button2.callback(self.button_event, "button2")
        self.button3 = DebouncedSwitch(Pin(14, Pin.IN, Pin.PULL_DOWN), None)
        self.button3.callback(self.button_event, "button3")
        self.button4 = DebouncedSwitch(Pin(15, Pin.IN, Pin.PULL_DOWN), None)
        self.button4.callback(self.button_event, "button4")
        
        
        
        # Timer based display rendering
        timer1 = Timer()
        timer1.init(period=100, callback=self.render_full_display)


    # Clear the display
    def reset(self) -> None:
        self.spi_bus.write(bytearray([0xFF]))
        for _ in range(12):
            self.spi_bus.write(bytearray([0x00]))
        self.latch_pin.off()
        self.latch_pin.on()
        self.latch_pin.off()

    # Enable all LEDs for debugging
    def all_leds_on(self) -> None:
        self.spi_bus.write(bytearray([0x00]))
        for _ in range(12):
            self.spi_bus.write(bytearray([0xFF]))
        self.latch_pin.off()
        self.latch_pin.on()
        self.latch_pin.off()

    def _single_digit_to_byte(self, digit) -> int:
        mapping = {
            0: 190,
            1: 10,
            2: 230,
            3: 110,
            4: 90,
            5: 124,
            6: 252,
            7: 14,
            8: 254,
            9: 126,
            None: 0,
        }
        return int(mapping[digit])

    def _render_integer(self, display, blinky_time) -> list:
        if display["value"] < 0 or display["value"] > 1000:
            self.reset()
            raise ValueError
        # return all zeros if blink
        if display["blink"] and blinky_time:
            return [0, 0, 0]
        display_bytes = []
        display_string = f"{display['value']:03d}"
        for i in display_string:
            display_bytes.append(self._single_digit_to_byte(int(i)))
        return display_bytes

    def _render_float(self, display, blinky_time) -> list:
        # We only support 2 digits before the colon, and we will always take the first digit after the colon
        if int(math.log10(display["value"])) + 1 > 2:
            self.reset()
            raise ValueError
        # return all zeros if blink
        if display["blink"] and blinky_time:
            return [0, 0, 0]
        display_bytes = []
        display_string = f"{display['value']:4.1f}"
        digit = 0
        for i in display_string:
            if i == " ":
                i = 0
            if i == ".":
                continue
            if digit == 1:
                display_bytes.append(self._single_digit_to_byte(int(i)) + 1)
            else:
                display_bytes.append(self._single_digit_to_byte(int(i)))
            digit = digit + 1
        return display_bytes

    def render_full_display(self, timer) -> None:
        if time.time() % 2:
            blinky_time = True
        else:
            blinky_time = False

        output_buffer = []
        for display in [self.display1, self.display2, self.display3, self.display4]:
            if isinstance(display["value"], int):
                for byte in self._render_integer(display, blinky_time):
                    output_buffer.append(byte)
            if isinstance(display["value"], float):
                for byte in self._render_float(display, blinky_time):
                    output_buffer.append(byte)

        output_buffer.append(255)
        for button_led in [
            self.button1_led,
            self.button2_led,
            self.button3_led,
            self.button4_led,
        ]:
            if button_led["value"] and not (button_led["blink"] and blinky_time):
                output_buffer[-1] = output_buffer[-1] - button_led["address"]

        self.spi_bus.write(bytearray(reversed(output_buffer)))
        self.latch_pin.off()
        self.latch_pin.on()
        self.latch_pin.off()

    # Overwrite these functions in your base application
    def rotary_event(self) -> None:
        self.logger.debug('Rotary Event occured')
        for rotary in [self.rotary_1, self.rotary_2, self.rotary_3, self.rotary_4]:
            if rotary.value() != 0:
                self.logger.debug(f'Encoder {rotary.id} value change: {rotary.value()}')
                rotary.set(value=0)
                
    def button_event(self, pin) -> None:
        self.logger.debug(f'Button Event occured on {pin}')

