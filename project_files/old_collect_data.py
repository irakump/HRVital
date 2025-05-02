from fifo import Fifo
from piotimer import Piotimer
from machine import Pin, ADC, I2C
from ssd1306 import SSD1306_I2C


class PulseSensorData:
    def __init__(self, size, adc_pin_nr):
        self.fifo = Fifo(size, typecode = 'i')
        self.av = ADC(adc_pin_nr) # sensor AD channel

    def handler(self, tid):
        # handler to read and store ADC value
        self.fifo.put(self.av.read_u16())


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
    
    tmr.deinit()  # stop timer to disable handler
    return samples


#samples = collect_data_n_seconds()
#print(len(samples))  # verify that got 7500 samples in 30s
