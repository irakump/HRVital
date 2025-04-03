'''Implement a program that finds positive peaks from a test signal using slope inspection.
The test signal(s) contain pure sine wave so the peaks can be found by inspecting
the slope of the signal without using a threshold. The peak is at a point where the slope turns from positive to negative.
Your program must print at least three peak-to-peak intervals both in number of samples and seconds and to calculate the frequency of the signal.'''

from filefifo import Filefifo
data = Filefifo(10, name = 'capture_250Hz_01.txt')
    
previous_sample = data.get()
current_sample = data.get()
sample_count = 2   #track sample position

sampling_rate_hz = 250

peaks = []

while len(peaks) < 6:    
    next_sample = data.get()
    sample_count += 1
    
    if (current_sample > previous_sample) and (current_sample >= next_sample):   # peak detection
        peaks.append(sample_count-1)     #positioning because already incremented
        print(f"Peak at {sample_count-1} (value: {current_sample})")
        
    previous_sample = current_sample
    current_sample = next_sample
    
print('\nPeak-to-peak Interval:')
list_samples = []
interval_seconds = []

for i in range(4):
    interval_samples = peaks[i + 1] - peaks[i] #samples between two peaks (peak1 - peak0, peak2 - peak1)
    list_samples.append(interval_samples)
    interval_period = interval_samples/sampling_rate_hz #sample to second T=1/f (250sample = 1second)(1sample/250 =0.004sec)
    
    print(f"PPI {i +1}: {interval_samples} samples, {interval_period:.3f} seconds")
    interval_seconds.append(interval_period)

avg_interval_period = sum(interval_seconds)/ len(interval_seconds) #sekuntien summa/sekuntienlukumäärä

frequency = 1 / avg_interval_period   #f=1/T
print(f"Frequency: {frequency:.3f} Hz")




