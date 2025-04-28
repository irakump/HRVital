from time import ticks_ms, ticks_diff, sleep
from ssd1306 import SSD1306_I2C
from machine import Pin, I2C, ADC
from piotimer import Piotimer
from fifo import Fifo
import array
import micropython
micropython.alloc_emergency_exception_buf(200)

class HR:
    def __init__(self):
        self.i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
        self.oled = SSD1306_I2C(128, 64, self.i2c)
        self.sensor = ADC(Pin(26))
        self.button = Pin(12, Pin.IN, Pin.PULL_UP)

        # Buffers & state
        self.samples_fifo = Fifo(1500, 'H')  #stores 1500 ADC samples
        self.filtered = array.array('H', [0]*750)  # 750 filtered samples circular buffer
        self.write_index = 0           # Current position in circular buffer
        self.peaks = array.array('I', [0]*10)   # Stores up to 10 peak positions
        self.peak_count = 0

        # Display configuration
        self.width = 128
        self.ppg_buf = array.array('H', [0]*self.width)  # for displayed waveform
        self.last_ppg_update = ticks_ms()
        self.ppg_update_interval = 100  #update wavefor evey 100ms

        # BPM calculation 
        self.bpm_history = array.array('H', [0]*7)  # Stores last 7 BPM readings
        self.bpm_index = 0
        self.display_bpm = 0
        self.last_valid_bpm = 0
        self.first_valid = False
        self.last_bpm_update = ticks_ms()
        self.bpm_update_interval = 5000   # bpm update every 5 sec

        # Control flags
        self.measuring = False
        self.button_flag = False
        self.last_button_check = ticks_ms()
        self.debounce_ms = 200

        self.timer = Piotimer(freq=250, mode=Piotimer.PERIODIC, callback=self.sample_isr)
        self.show_menu()
        
    # Interrupt service routine
    def sample_isr(self, timer):
        try:
            self.samples_fifo.put(self.sensor.read_u16())  
        except Exception as e:
            pass
        self.button_flag = not self.button.value()  #check button state

    # Display the start menu screen
    def show_menu(self):
        self.oled.fill(0)
        self.oled.text("Measure HR", 20, 10)
        self.oled.text("Press to START", 5, 30)
        self.oled.show()

    #Draw the PPG wave and BPM information
    def draw_display(self, bpm):
        mn = min(self.ppg_buf)   # Calculate display sclaing
        mx = max(self.ppg_buf)
        span = mx - mn or 1    #prevent division by 0
        
        #Draw PPG wave
        self.oled.fill(0)
        prev_y = None
        for x, raw in enumerate(self.ppg_buf):
            y = 63 - int((raw - mn) * 63 // span)
            if prev_y is not None:
                self.oled.line(x-1, prev_y, x, y, 1)
            prev_y = y
        
        # Display BPM 
        if bpm > 0:
            self.oled.text(f"{bpm} bpm", 0, 0)
            bar_width = min(128, max(10, (mx - mn) // 100))  #signal quality bar/line
            self.oled.rect(0, 10, bar_width, 3, 1)
        else:
            if self.first_valid:
                self.oled.text(f"{self.last_valid_bpm} bpm", 0, 0)
            else:
                self.oled.text("Place finger", 0, 0)
        
        self.oled.show()

    #Process samples from fifo buffer
    def process_samples(self):
        count = 0
        while self.samples_fifo.has_data() and count < 750:   
            self.filtered[(self.write_index + count) % 750] = self.samples_fifo.get()
            count += 1
        self.write_index = (self.write_index + count) % 750
        return count

    # 3-point weighted moving average filter
    def smooth_signal(self):
        for i in range(2, len(self.filtered)):         #Weights: [1, 2, 1] normalized by dividing 4
            self.filtered[i] = (self.filtered[i-2] + 2*self.filtered[i-1] + self.filtered[i]) // 4

    #Detects peaks and calculate hr
    def calculate_bpm(self):
        if not self.process_samples():
            return 0
        
        self.smooth_signal()
        
        # Threshold calculation, use 10 and 90 percentile to ignore outliers
        sorted_samples = sorted(self.filtered)  
        threshold = sorted_samples[len(sorted_samples)//10] + \
                    (sorted_samples[len(sorted_samples)*9//10] - \
                   sorted_samples[len(sorted_samples)//10]) * 8 // 10
 
        # Peak detection
        self.peak_count = 0
        prev = self.filtered[0]
        rising = False
        last_peak = -1000    #impossible value
        
        for i in range(1, len(self.filtered)):
            curr = self.filtered[i]
            if curr > threshold and prev <= threshold and rising:  # Detect threshold crossing with positive slope
                if (i - last_peak) > 150:  # Check if peak is enough spaced
                    if self.peak_count < len(self.peaks):
                        self.peaks[self.peak_count] = i   # Store peak position
                        self.peak_count += 1
                        last_peak = i
                rising = False
            elif curr > prev:
                rising = True
            prev = curr

        if self.peak_count >= 4:      # if at least 4 peaks detected, calculate bpm based on intervals between peaks
            intervals = []
            for j in range(1, self.peak_count):
                interval = self.peaks[j] - self.peaks[j-1]
                if 62 < interval < 375:    # intervals (40-240bpm at 250hz)
                    intervals.append(interval)
            
            if len(intervals) >= 3:  # At least 3 valid interval
                return (60 * 250) // sorted(intervals)[len(intervals)//2] #convert bpm based on the median interval(60 sec*250 samples/sec)/interval
        
        return 0
        
    def run(self):
        while True:
            now = ticks_ms()
            
            # Button handling
            if ticks_diff(now, self.last_button_check) > self.debounce_ms:
                self.last_button_check = now
                if self.button_flag:
                    self.button_flag = False
                    self.measuring = not self.measuring   #Toggle state
                    if not self.measuring:
                        self.show_menu()
                    else:                # reset states when starting measurement
                        self.first_valid = False
                        self.bpm_index = 0
                        for i in range(len(self.bpm_history)):
                            self.bpm_history[i] = 0
                        self.last_bpm_update = now

            if self.measuring:
                current_bpm = self.calculate_bpm()
                
                # update bpm if valid reading
                if current_bpm > 0:
                    self.bpm_history[self.bpm_index] = current_bpm
                    self.bpm_index = (self.bpm_index + 1) % len(self.bpm_history)
                    self.first_valid = True
                    self.last_valid_bpm = current_bpm

               # 5 sec BPM update
                if ticks_diff(now, self.last_bpm_update) >= self.bpm_update_interval:
                    self.last_bpm_update = now  # Reset timer first
                    if self.first_valid:
                        valid = sorted([b for b in self.bpm_history if b > 0])  #calculate median of valid readings
                        if len(valid) >= 3:
                            self.display_bpm = valid[len(valid)//2]
                    #print(self.display_bpm)       
                    self.draw_display(self.display_bpm)  # Forcing display update

                # waveform update (every100 ms)
                if ticks_diff(now, self.last_ppg_update) >= self.ppg_update_interval:
                    self.last_ppg_update = now
                    for i in range(self.width):
                        index = (self.write_index - (self.width - i) * 5) % 750
                        self.ppg_buf[i] = self.filtered[index]
                    self.draw_display(self.display_bpm)

            sleep(0.01)

hr = HR()
hr.run()