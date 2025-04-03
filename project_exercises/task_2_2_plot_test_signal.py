from filefifo import Filefifo

"""
Task 2.2
Implement a program that reads test signal from the file, scales it to range 0 – 100 and prints the scaled
values to console. Remember to enable Plotter in Thonny to see the graph.

Start by reading two seconds of data and find minimum and maximum values from the data. Then use
min and max values to scale the data so that minimum value is printed as zero and maximum value as
100. Plot 10 seconds of data with the scaling.
"""

file_name = 'capture_250Hz_02.txt'
data = Filefifo(10, name = file_name)

samples = []

for sample in range(500): # 2 seconds of data (T = 1/f => N = T*f = 2*250 = 500 samples)
    samples.append(data.get()) # save samples into a list

min_value = min(samples)
max_value = max(samples)

data2 = Filefifo(10, name = file_name) # start from the first sample

for sample in range(2500): # 10 seconds of data (N = T*f = 10*250 = 2500)
    value = data2.get()
    scaled_value = (value - min_value) / (max_value - min_value) * 100 # scale the values to range 0 - 100
    print(scaled_value)
