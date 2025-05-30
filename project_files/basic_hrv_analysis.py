from fifo import Fifo
from piotimer import Piotimer
from machine import Pin, ADC, I2C
from ssd1306 import SSD1306_I2C
import time

from collect_data_v2 import collect_data_n_seconds
from mqtt import Mqtt


class HeartRate:
    def __init__(self):
        self.sample_rate = 250  # 250 samples per sec
        self.threshold = None    # threshold for peak detection
        self.min_peak_distance = 0.4 * self.sample_rate # minimum gap between detected peaks (0.4s)
    
    # calculate dynamic threshold using first sec of data
    def threshold_calculation(self, samples):
        avg_value = sum(samples) / (len(samples))    # average signal value
        dynamic_range = (max(samples) - avg_value)   # range above avg_value
        threshold = avg_value + 0.8 * dynamic_range # average value + half dynamic range
        return threshold
        
    # main - analyze peaks in signal
    def find_peaks(self, samples):
        peaks = []
        previous_sample = samples[0]
        increasing = False # track if rising signal
        
        # initial treshold from first 250 samples
        self.threshold = self.threshold_calculation(samples[:self.sample_rate])
        
        for i, sample in enumerate(samples):
            if i > 0 and i % self.sample_rate == 0:
                self.threshold = self.threshold_calculation(samples[i-self.sample_rate:i])
            
            if sample > self.threshold and previous_sample <= self.threshold and increasing: # check if valid peak
                if not peaks or (i - peaks[-1]) > self.min_peak_distance:   # ensuring peaks far enough from the last one 
                    peaks.append(i)
  
                increasing = False
            elif sample > previous_sample:
                increasing = True
            previous_sample = sample
        return peaks


class BasicHRVAnalysis:
    def __init__(self):
        self.freq = 250
        self.valid_lowest_ppi = 300  # equal to 30bpm
        self.valid_highest_ppi = 2400  # equal to 240bpm
        self.adjacent_ppis_max_diff_percent = 0.2  # 20 %
    
    def get_ppis(self, peaks):
        all_ppis = []
        # calculate ppi for each peak
        for i in range(len(peaks) - 1):
            interval_samples = peaks[i + 1] - peaks[i]  # samples between two consecutive peaks
            ppi = interval_samples / self.freq * 1000  # samples in ms
            all_ppis.append(int(ppi))
        return all_ppis
    
    # discard abnormally high or low ppis
    def clean_ppis(self, all_ppis):
        # discard ppis which are lower than lowest and higher than highest possible ppis
        all_ppis = [int(ppi) for ppi in all_ppis if self.valid_lowest_ppi <= ppi <= self.valid_highest_ppi]
        
        # save ppis that are within 20% of adjacent ppi
        valid_ppis = []
        for index in range(1, len(all_ppis) - 1):
            ppi = all_ppis[index]
            # get last valid ppi if exists else get previous ppi
            previous_ppi = valid_ppis[-1] if valid_ppis else all_ppis[index - 1]
            
            # check if adjacent ppis are within 20% of each other
            def check_if_ppis_within_x_percent_of_each_other(ppi, previous_ppi):
                return abs(ppi - previous_ppi) <= self.adjacent_ppis_max_diff_percent * max(ppi, previous_ppi)
            
            # perform check for ppi and last valid ppi
            if check_if_ppis_within_x_percent_of_each_other(ppi, previous_ppi):
                if index == 1:  # add ppi at index 0 if index is 1
                    valid_ppis.append(previous_ppi)
                valid_ppis.append(ppi)
            else:
                # perform check for ppi and previous ppi
                previous_ppi = all_ppis[index - 1]
                if check_if_ppis_within_x_percent_of_each_other(ppi, previous_ppi):
                    if valid_ppis[-1] != previous_ppi:
                        valid_ppis.append(previous_ppi)
                    valid_ppis.append(ppi)
        
        return valid_ppis

    def get_mean_ppi(self, all_ppis):
        # get mean ppi of all ppis
        return sum(all_ppis) / len(all_ppis)

    def get_rmssd(self, all_ppis):
        # root mean square of successive differences:
        # subtract previous peak from next peak and calculate squared difference between those peaks
        diffs = [(all_ppis[i+1] - all_ppis[i])**2 for i in range(len(all_ppis) - 1)]
        return (sum(diffs) / len(diffs))**0.5  # mean diff root

    def get_sdnn(self, all_ppis, mean_ppi):
        # standard deviation of nn intervals:
        # subtract mean ppi from each ppi, square the subtraction and calculate sum of the results
        # calculate mean of the sum and square root of the mean
        return (sum([(ppi - mean_ppi)**2 for ppi in all_ppis]) / (len(all_ppis)))**(0.5)

    def get_basic_hrv_analysis(self):
        data = collect_data_n_seconds(seconds=30)
        if not data:  # data collection canceled
            return None
        
        hr_class = HeartRate()
        peak_indexes = hr_class.find_peaks(data)
        #print('peaks', len(peak_indexes), peak_indexes)
        
        all_ppis = self.get_ppis(peak_indexes)  # in ms
        #print('all_ppis before discard', len(all_ppis), all_ppis)
        
        cleaned_ppis = self.clean_ppis(all_ppis)
        #print('all_ppis', len(cleaned_ppis), cleaned_ppis)
        
        if not cleaned_ppis:
            message = "Invalid result"
            Mqtt().send_basic_hrv_analysis_results_to_mqtt(message)
            return message
        
        mean_ppi = self.get_mean_ppi(cleaned_ppis)
        print(f'mean_ppi: {mean_ppi:.0f}')
        
        rmssd = self.get_rmssd(cleaned_ppis)
        print(f'rmssd: {rmssd:.0f}')
        
        sdnn = self.get_sdnn(cleaned_ppis, mean_ppi)
        print(f'sdnn: {sdnn:.0f}')
        
        hrs = [round(60000 / ppi) for ppi in cleaned_ppis]
        print('hrs', hrs)
        mean_hr = sum(hrs) / len(hrs)
        print(f'mean_hr: {mean_hr:.0f}')
        
        # send results to mqtt
        message = {"mean_hr": int(mean_hr), "mean_ppi": int(mean_ppi), "rmssd": int(rmssd), "sdnn": int(sdnn)}
        Mqtt().send_basic_hrv_analysis_results_to_mqtt(message)
        
        # return calculated values
        return (int(mean_hr), int(mean_ppi), int(rmssd), int(sdnn))
