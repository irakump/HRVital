from fifo import Fifo
from piotimer import Piotimer
from machine import Pin, ADC, I2C
from ssd1306 import SSD1306_I2C


### ongelma ###
# kun mittarista päästää irti kesken mittauksen ja laittaa sormen takaisin,
# signaalista erottaa harvoin sykettä
# signaali on siis niin sanotusti pilalla, mutta miksi?

# kysymys: saako handlerissä käsitellä virheitä?


class isr_fifo(Fifo):
    def __init__(self, size, adc_pin_nr):
        super().__init__(size, typecode = 'i')
        self.av = ADC(adc_pin_nr) # sensor AD channel

    def handler(self, tid):
        # handler to read and store ADC value
        try:
            self.put(self.av.read_u16())
        except RuntimeError:
            # empty fifo when it gets full
            while self.has_data():
                self.get()


pin_nr = 27
data = isr_fifo(50, pin_nr) # create the improved fifo: size = 50, adc pin = pin_nr
tmr = Piotimer(mode = Piotimer.PERIODIC, freq = 250, callback = data.handler)


i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)


def show_oled(samples):
    oled.fill(0)
    x = 0
    previous_sample = False
    
    # display samples
    for sample in samples:
        if previous_sample:
            # display line from previous sample (x, y) to current sample (x, y)
            oled.line(x - 1, previous_sample, x, sample, 1)
        previous_sample = sample
        x += 1
    oled.show()


def get_min_max_range_and_treshold(samples):
    min_sample, max_sample = min(samples), max(samples)
    sample_range = max_sample - min_sample
    treshold = min_sample + 0.80 * sample_range
    return min_sample, max_sample, sample_range, treshold


def scale_sample_to_display_height(sample, min_sample, sample_range):
    scaled_sample = (sample - min_sample) / sample_range * (oled_height - 1)
    # prevent sample going above or below min or max
    scaled_sample = min(oled_height - 1, max(1, scaled_sample))
    return int(scaled_sample)


class ScaleSamples:
    def __init__(self):
        self.min_sample = False
        self.max_sample = False
        self.sample_range = False
        self.treshold = False
    
    def scale_samples(self, samples, previous_samples, calculate_new_treshold):
        # samples is always 5 in this example
        
        # calculate min, max, range and treshold from previous 250 samples (or from beginning if none)
        if calculate_new_treshold or not any([self.min_sample, self.max_sample, self.sample_range, self.treshold]):
            self.min_sample, self.max_sample, self.sample_range, self.treshold = get_min_max_range_and_treshold(previous_samples)
        
        # scale samples horizontally
        scaled_sample = int(sum(samples) / 5)
        
        # scale samples vertically to display height
        scaled_sample = scale_sample_to_display_height(scaled_sample, self.min_sample, self.sample_range)
        return scaled_sample


oled.fill(0)
freq = 250  # 1 second

scale_samples_class = ScaleSamples()
calculate_new_treshold = False
index = 0

five_samples = []
previous_250_samples = []
scaled_samples = []

while True:
    if not data.empty():
        index += 1
        
        # save five successive samples to list
        if len(five_samples) == 5:
            previous_250_samples.extend(five_samples)  # add deleted five samples to previous 250 samples
            five_samples.clear()
            
            # delete five samples from beginning after adding five samples to end
            del previous_250_samples[:4]
        five_samples.append(data.get())
        
        # reset loop
        if len(five_samples) != 5 or len(previous_250_samples) < 250:
            continue
        
        # calculate new treshold every 250 samples
        calculate_new_treshold = True if index % 250 == 0 else False
        
        # scale five samples to one
        scaled_sample = scale_samples_class.scale_samples(five_samples, previous_250_samples, calculate_new_treshold)
        scaled_samples.append(scaled_sample)
        
        # delete sample from beginning of list if list is larger than display width
        if len(scaled_samples) > oled_width:
            scaled_samples.pop(0)
        
        show_oled(scaled_samples)
