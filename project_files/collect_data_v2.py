from fifo import Fifo
from piotimer import Piotimer
from machine import Pin, ADC, I2C
from ssd1306 import SSD1306_I2C
import time

class PulseSensorData:
    def __init__(self, size, adc_pin_nr):
        self.fifo = Fifo(size, typecode = 'i')
        self.av = ADC(adc_pin_nr) # sensor AD channel
        
        # button handler
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
        
        # user action detection (go back to main menu if user pressed button)
        if not data.button_fifo.empty():
            button_value = data.button_fifo.get()
            print(button_value)

            if button_value == 0:
               tmr.deinit()
               return None # measurement stopped
    
    tmr.deinit()  # stop timer to disable handler
    return samples
