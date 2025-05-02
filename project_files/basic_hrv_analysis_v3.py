from fifo import Fifo
from piotimer import Piotimer
from machine import Pin, ADC, I2C
from ssd1306 import SSD1306_I2C
import time

#from collect_data import collect_data_n_seconds # original
from collect_data_v2 import collect_data_n_seconds # uusi, testi
from live_pulse import ScaleSamples

from mqtt import Mqtt


class HeartRate:
    def __init__(self):
        self.sample_rate = 250  #250 samples per sec
        self.threshold = None    #threshold for peak detection
        self.min_peak_distance = 0.4 * self.sample_rate #minimum gap between detected peaks (0.4s)
    
    #calculate dynamic threshold using first sec of data
    def threshold_calculation(self, samples):
        avg_value = sum(samples) / (len(samples))    #average signal value
        dynamic_range = (max(samples) - avg_value)   #range above avg_value
        threshold = avg_value + 0.8 * dynamic_range #average value + half dynamic range
        return threshold
        
    #main - analyze peaks in signal
    def find_peaks(self, samples):
        peaks = []
        previous_sample = samples[0]
        increasing = False #track if rising signal
        
        # initial treshold from first 250 samples
        self.threshold = self.threshold_calculation(samples[:250])
        
        for i, sample in enumerate(samples):
            if i > 0 and i % 250 == 0:
                self.threshold = self.threshold_calculation(samples[i-250:i])
            
            if sample > self.threshold and previous_sample <= self.threshold and increasing: #check if valid peak
                if not peaks or (i - peaks[-1]) > self.min_peak_distance:   # ensuring peaks far enough from the last one 
                    peaks.append(i)
                    
                    # älä poista vielä
                    """
                    # discard potential peaks that are too different from previous couple of peaks
                    if len(peaks) >= 2:
                        # subtract two previous peaks and calculate absolute value
                        # subtract current sample index and previous peak and calculate absolute value
                        abs_two_previous_peaks = abs(peaks[-1] - peaks[-2])
                        abs_potential_peak_and_previous_peak = abs(peaks[-1] - i)
                        print('abs_two_previous_peaks', abs_two_previous_peaks)
                        print('abs_potential_peak_and_previous_peak', abs_potential_peak_and_previous_peak)

                        # register peak if abs_potential_peak_and_previous_peak is within 10% of abs_two_previous_peaks
                        # muokkaa prosenttia jos tarpeen
                        if abs(abs_two_previous_peaks - abs_potential_peak_and_previous_peak) <= 0.2 * abs_two_previous_peaks:
                            peaks.append(i)
                    else:"""
                    
                    
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
    
    def get_ppis(self, peaks):
        all_ppis = []
        
        # calculate ppi for each peak
        for i in range(len(peaks) - 1):
            interval_samples = peaks[i + 1] - peaks[i]  # samples between two consecutive peaks
            ppi = interval_samples / self.freq * 1000  # samples in ms
            all_ppis.append(int(ppi))
        
        print('all_ppis before discard', len(all_ppis), all_ppis)
        
        ### to-do: get new mean ppi every 5 ppis for more accurate mean value
        # reason: when too many high ppi values present in initial ppis,
        # it results in too high rmssd and sdnn values
        
        # discard abnormally high or low ppis
        #mean_ppi = self.get_mean_ppi(all_ppis)
        """
        variability_range = 200
        low = mean_ppi - variability_range
        high = mean_ppi + variability_range
        print(low, high, mean_ppi)
        """
        
        # discard ppis which are lower than lowest and higher than highest possible ppis
        all_ppis = [int(ppi) for ppi in all_ppis if self.valid_lowest_ppi <= ppi <= self.valid_highest_ppi]
        
        valid_ppis = []
        for index in range(1, len(all_ppis) - 1):
            ppi = all_ppis[index]
            previous_ppi = all_ppis[index - 1]
            #print(ppi, previous_ppi)
            # check if adjacent ppis are within 20% of each other
            if abs(ppi - previous_ppi) <= 0.2 * max(ppi, previous_ppi):
                valid_ppis.append(int(ppi))
            
            
        # discard ppis which differ more than 20% from previous ppi
        #all_ppis = [all_ppis[index] for index in range(1, len(all_ppis) - 1) if ]
        
        print('all_ppis after discard', len(valid_ppis), valid_ppis)
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
        #print(len(data))
        if data is None:
            return None
        
        
        hr_class = HeartRate()
        peak_indexes = hr_class.find_peaks(data)
        print('peaks', len(peak_indexes), peak_indexes)
        
        all_ppis = self.get_ppis(peak_indexes)  # in ms
        print('all_ppis', all_ppis)
        
        mean_ppi = self.get_mean_ppi(all_ppis)
        print(f'mean_ppi: {mean_ppi:.0f}')
        
        rmssd = self.get_rmssd(all_ppis)
        print(f'rmssd: {rmssd:.0f}')
        
        sdnn = self.get_sdnn(all_ppis, mean_ppi)
        print(f'sdnn: {sdnn:.0f}')
        
        hrs = [round(60000 / ppi) for ppi in all_ppis]
        print('hrs', hrs)
        mean_hr = sum(hrs) / len(hrs)
        print(f'mean_hr: {mean_hr:.0f}')
        
        #kubios_result = Mqtt().get_kubios_analysis_result(all_ppis)
        #print(kubios_result)
        
        # testaamiseen, jätä! älä poista lopullisesta versiosta
        message = {"mean_hr": mean_hr, "mean_ppi": mean_ppi, "rmssd": rmssd, "sdnn": sdnn}
        Mqtt().send_basic_hrv_analysis_results_to_mqtt(message)
        
        # return calculated values


        return (int(mean_hr), int(mean_ppi), int(rmssd), int(sdnn))
        #return (all_ppis) # tämä pitää palauttaa kubiosta varten!

#BasicHRVAnalysis().get_basic_hrv_analysis()