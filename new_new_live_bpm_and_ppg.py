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


def show_ppg_signal_on_oled(samples, bpm):
    oled.fill(0)
    oled.text(f'{bpm} BPM', 0, 0)
    
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


class HeartRate:
    def __init__(self, freq, fifo_size, pin):
        self.freq = freq
        self.fifo_size = fifo_size
        self.pin = pin
        
        self.min_sample = False
        self.max_sample = False
        self.sample_range = False
        self.threshold = False
        self.threshold_percentage = 0.90
        self.min_peak_distance = 0.4 * self.freq  # minimum gap between detected peaks (0.4s * freq)
        
        self.min_valid_bpm = 30
        self.max_valid_bpm = 240
        
        self.min_peaks_for_valid_hr = 3
    
    def calculate_min_max_range_and_threshold(self, samples):
        self.min_sample, self.max_sample = min(samples), max(samples)
        self.sample_range = self.max_sample - self.min_sample
        self.threshold = self.min_sample + self.threshold_percentage * self.sample_range

    def scale_sample_to_display_height(self, sample):
        # pixels to leave for bpm display
        bpm_pixel_reservation = 10
        
        scaled_sample = (sample - self.min_sample) / self.sample_range * (oled_height - 1 - bpm_pixel_reservation)
        # prevent sample going above or below min or max
        scaled_sample = min(oled_height - 1 - bpm_pixel_reservation, max(1, scaled_sample))
        return int(scaled_sample)
    
    def scale_five_samples_to_one(self, fifo, calculate_new_threshold):
        fifo_head_index = fifo.head  # index of newest value in fifo
        
        # calculate min, max, range and threshold from previous 250 samples
        if calculate_new_threshold or not any([self.min_sample, self.max_sample, self.sample_range, self.threshold]):
            last_250_samples = self.get_last_n_samples(fifo, 250)
            self.calculate_min_max_range_and_threshold(last_250_samples)
        
        # get last five samples and scale them horizontally
        # no need to do complex index calculation that last_250_samples required
        five_samples = fifo.data[fifo_head_index-5:fifo_head_index]
        scaled_sample = int(sum(five_samples) / 5)
        
        # scale samples vertically to display height
        scaled_sample = self.scale_sample_to_display_height(scaled_sample)
        return scaled_sample


    def get_last_n_samples(self, fifo, n):
        fifo_head_index = fifo.head  # index of newest value in fifo
        
        # save last n samples from fifo to list
        # from n indexes before current head index to current head index
        last_n_samples = fifo.data[fifo_head_index*(-1):fifo_head_index]
        
        # check if got n samples
        difference = fifo.size - len(last_n_samples)
            
        # if difference is more than 0, means fifo_head_index is less than n,
        # then get the difference from end of list by the same amount
        # so that last_n_samples is actually n values long
        if difference > 0:
            last_n_samples.extend(fifo.data[difference*(-1):])
            
        return last_n_samples
    
    
    def find_peaks(self, samples):
        peaks = []
        previous_sample = samples[0]
        increasing = False #track if rising signal
        
        # initial threshold from first 250 samples
        self.calculate_min_max_range_and_threshold(samples[:self.freq])
        
        for i, sample in enumerate(samples):
            if i > 0 and i % self.freq == 0:
                self.calculate_min_max_range_and_threshold(samples[i-self.freq:i])
            
            if sample > self.threshold and previous_sample <= self.threshold and increasing: #check if valid peak
                if not peaks or (i - peaks[-1]) > self.min_peak_distance:   # ensuring peaks far enough from the last one 
                    peaks.append(i)

                increasing = False
            elif sample > previous_sample:
                increasing = True
            previous_sample = sample
        return peaks


    def calculate_bmp(self, fifo):
        samples = self.get_last_n_samples(fifo, fifo.size)
        peaks = self.find_peaks(samples)
        
        if len(peaks) >= self.min_peaks_for_valid_hr:
            intervals = [peaks[i] - peaks[i-1] for i in range(1, len(peaks))]  # time between peaks
            avg_interval = sum(intervals) / len(intervals)
            bpm = 60 / (avg_interval / self.freq)  # heart rate in bpm
        else:
            bpm = 0  # if fewer than min_peaks_for_valid_hr
        
        # return bpm if valid, otherwise string "Invalid"
        if self.min_valid_bpm <= bpm <= self.max_valid_bpm:
            return round(bpm)
        return "Invalid"
    
    def show_live_bpm_and_ppg(self):
        # measing message at start
        oled.fill(0)
        oled.text("Measuring...", 8, 10)
        oled.show()
        
        data = PulseSensorData(self.fifo_size, self.pin)
        tmr = Piotimer(mode = Piotimer.PERIODIC, freq = self.freq, callback = data.handler)
        
        calculate_new_threshold = False
        threshold_calculation_freq_ms = 1000
        last_threshold_calculation_time = False
        
        scaled_samples = []
        fifo_filled_at_least_once = False
        
        bpm = False
        bpm_calculation_freq_ms = 3000
        last_bpm_calculation_time = False

        while True:
            if not data.fifo.empty():
                # get first sample from fifo (to empty fifo)
                data.fifo.get()
            
                # get current head index (index of fifo where new data is added)
                head_index = data.fifo.head
            
                # log that fifo has been filled at least once when that happens
                if not fifo_filled_at_least_once:
                    if head_index == fifo_size - 1:  # check if fifo has been filled once (head index is same as size - 1)
                        fifo_filled_at_least_once = True
                    else:
                        continue
            
                # scale last five samples every fifth sample and only if at least 1 second has passed from start
                if head_index % 5 == 0:
                
                    # calculate new threshold every n ms
                    timestamp = time.ticks_ms()
                    calculate_new_threshold = (timestamp - last_threshold_calculation_time) >= threshold_calculation_freq_ms
                    if calculate_new_threshold:
                        last_threshold_calculation_time = timestamp
                
                    # scale five samples to one
                    scaled_sample = self.scale_five_samples_to_one(data.fifo, calculate_new_threshold)
                    scaled_samples.append(scaled_sample)
                
                    # delete sample from beginning of list if list is larger than display width
                    if len(scaled_samples) > oled_width:
                        scaled_samples.pop(0)
                    
                    # calculate bpm every n ms
                    calculate_new_bpm = (timestamp - last_bpm_calculation_time) >= bpm_calculation_freq_ms
                    if calculate_new_bpm:
                        last_bpm_calculation_time = timestamp
                    if calculate_new_bpm:
                        bpm = self.calculate_bmp(data.fifo)
                    
                    # show bpm and ppg on display
                    show_ppg_signal_on_oled(scaled_samples, bpm)


pin = 27
fifo_size = 750
freq = 250

HeartRate(freq, fifo_size, pin).show_live_bpm_and_ppg()
