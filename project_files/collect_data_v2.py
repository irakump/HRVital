from fifo import Fifo
from piotimer import Piotimer
from machine import Pin, ADC, I2C
from ssd1306 import SSD1306_I2C
import time
#from oled import Encoder # rotary encoder -> poista?

# kopioitu, poista
class Encoder:
    def __init__(self):
        self.a = Pin(10, mode = Pin.IN, pull = Pin.PULL_UP)
        self.b = Pin(11, mode = Pin.IN, pull = Pin.PULL_UP)
        self.a.irq(handler = self.scroll_handler, trigger = Pin.IRQ_RISING, hard = True)
        
        self.button = Pin(12, Pin.IN, Pin.PULL_UP)
        self.button.irq(handler = self.button_handler, trigger = Pin.IRQ_RISING, hard = True)
        self.previous_button_press_timestamp = 0
        
        self.fifo = Fifo(30, typecode = 'i')
        
    def scroll_handler(self, pin):
        if self.b():
            self.fifo.put(-1)
        else:
            self.fifo.put(1)
    
    def button_handler(self, button):
        current_timestamp = time.ticks_ms()
        # ignore button press if less than 300 ms from previous
        if time.ticks_diff(current_timestamp, self.previous_button_press_timestamp) > 300:
            self.fifo.put(0)
            self.previous_button_press_timestamp = current_timestamp
        else:
            self.fifo.put(-2)
            
    def clear(self): # clear the fifo
        while self.fifo.has_data():
            x = self.fifo.get()
########################

class PulseSensorData:
    def __init__(self, size, adc_pin_nr):
        self.fifo = Fifo(size, typecode = 'i')
        self.av = ADC(adc_pin_nr) # sensor AD channel
        
        # for button handler
        self.button = Pin(12, Pin.IN, Pin.PULL_UP)
        self.button.irq(handler = self.button_handler, trigger = Pin.IRQ_RISING, hard = True)
        self.previous_button_press_timestamp = 0
        
        self.button_fifo = Fifo(30, typecode = 'i')

    def handler(self, tid):
        # handler to read and store ADC value
        self.fifo.put(self.av.read_u16())

    def button_handler(self, button):
        current_timestamp = time.ticks_ms()
        # ignore button press if less than 300 ms from previous
        if time.ticks_diff(current_timestamp, self.previous_button_press_timestamp) > 300:
            self.button_fifo.put(0)
            self.previous_button_press_timestamp = current_timestamp
        else:
            self.button_fifo.put(-2)

def collect_data_n_seconds(seconds=30):
    data = PulseSensorData(750, 27)  # fifo size = 750, pin number = 27
    tmr = Piotimer(mode = Piotimer.PERIODIC, freq = 250, callback = data.handler)

    freq = 250  # samples in 1s
    samples_in_seconds = freq * seconds  # 7500 samples in 30 seconds
    samples = []
    
    # collect samples till collected samples count equals samples_in_seconds
    while len(samples) != samples_in_seconds:
        if not data.fifo.empty():
            samples.append(data.fifo.get())
        
        
        # user action detection -> jos painaa nappia, pitäisi palata menuun
        if not data.button_fifo.empty():
            button_value = data.button_fifo.get()
            print(button_value)
            # jos value == 0: main menu -> logiikka on menu.py (ei voi importata??)
            if button_value == 0:
               tmr.deinit()
               return None # measurement stopped -> returns none
    
    tmr.deinit()  # stop timer to disable handler
    return samples


#samples = collect_data_n_seconds()
#print(len(samples))  # verify that got 7500 samples in 30s