from fifo import Fifo
from piotimer import Piotimer
from machine import Pin, ADC, I2C
from ssd1306 import SSD1306_I2C
import time


class PulseSensorData:
    def __init__(self, size, adc_pin_nr):
        self.fifo = Fifo(size, typecode = 'i')
        self.av = ADC(adc_pin_nr) # sensor AD channel

    def handler(self, tid):
        # handler to read and store ADC value
        self.fifo.put(self.av.read_u16())


# init oled display
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)


def show_ppg_signal_on_oled(samples):
    oled.fill(0)
    x = 0
    previous_sample = False
    
    # display samples
    for sample in samples:
        if previous_sample:
            # display line from previous sample (x, y) to current sample (x, y)
            # oled_height - previous_sample (and oled_height - sample) flips the pixels,
            # so peaks appear as peaks and not valleys
            oled.line(x - 1, oled_height - previous_sample, x, oled_height - sample, 1)
        previous_sample = sample
        x += 1
    oled.show()


class ScaleSamples:
    def __init__(self):
        self.min_sample = False
        self.max_sample = False
        self.sample_range = False
        self.treshold = False
        self.treshold_percentage = 0.90
    
    def calculate_min_max_range_and_treshold(self, samples_250):
        self.min_sample, self.max_sample = min(samples_250), max(samples_250)
        self.sample_range = self.max_sample - self.min_sample
        self.treshold = self.min_sample + self.treshold_percentage * self.sample_range

    def scale_sample_to_display_height(self, sample):
        scaled_sample = (sample - self.min_sample) / self.sample_range * (oled_height - 1)
        # prevent sample going above or below min or max
        scaled_sample = min(oled_height - 1, max(1, scaled_sample))
        return int(scaled_sample)
    
    def scale_five_samples_to_one(self, fifo, calculate_new_treshold):
        fifo_head_index = fifo.head  # index of newest value in fifo
        
        # calculate min, max, range and treshold from previous 250 samples
        if calculate_new_treshold or not any([self.min_sample, self.max_sample, self.sample_range, self.treshold]):

            # save last 250 samples from fifo to list
            # from 250 indexes before current head index to current head index
            last_250_samples = fifo.data[fifo_head_index-250:fifo_head_index]
            
            # get the difference of 250 and length of last_250_samples list
            difference = 250 - len(last_250_samples)
            
            # if difference is more than 0, means fifo_head_index is less than 249,
            # then get the difference from end of list by the same amount
            # so that last_250_samples is actually 250 values long
            if difference > 0:
                last_250_samples.extend(fifo.data[difference*(-1):])
            
            self.calculate_min_max_range_and_treshold(last_250_samples)
        
        # get last five samples and scale them horizontally
        # no need to do complex index calculation that last_250_samples required
        five_samples = fifo.data[fifo_head_index-5:fifo_head_index]
        scaled_sample = int(sum(five_samples) / 5)
        
        # scale samples vertically to display height
        scaled_sample = self.scale_sample_to_display_height(scaled_sample)
        return scaled_sample


def show_live_ppg_signal():
    oled.fill(0)
    
    data = PulseSensorData(750, 27)  # fifo size = 750, pin number = 27
    tmr = Piotimer(mode = Piotimer.PERIODIC, freq = 250, callback = data.handler)
    
    scale_samples = ScaleSamples()
    calculate_new_treshold = False
    last_treshold_calculation_time = False
    
    scaled_samples = []
    at_least_1s_passed = False

    while True:
        if not data.fifo.empty():
            # get first sample from fifo (to empty fifo)
            data.fifo.get()
        
            # get current head index (index of fifo where new data is added)
            head_index = data.fifo.head
            #print('head_index', head_index)
        
            # log that 1s has passed if not yet true when head_index passes 250 for the first time
            if not at_least_1s_passed:
                if head_index > 250:
                    at_least_1s_passed = True
        
            # scale last five samples every fifth sample and only if at least 1 second has passed from start
            if head_index % 5 == 0 and at_least_1s_passed:
            
                # calculate new treshold every 1000ms = 1s
                timestamp = time.ticks_ms()
                calculate_new_treshold = (timestamp - last_treshold_calculation_time) >= 1000
                if calculate_new_treshold:
                    last_treshold_calculation_time = timestamp
            
                # scale five samples to one
                scaled_sample = scale_samples.scale_five_samples_to_one(data.fifo, calculate_new_treshold)
                scaled_samples.append(scaled_sample)
            
                # delete sample from beginning of list if list is larger than display width
                if len(scaled_samples) > oled_width:
                    scaled_samples.pop(0)
            
                show_ppg_signal_on_oled(scaled_samples)


#show_live_ppg_signal()
