from time import ticks_ms, ticks_diff, sleep
from ssd1306 import SSD1306_I2C
from machine import Pin, I2C, ADC
from piotimer import Piotimer
import array
from fifo import Fifo
import micropython
micropython.alloc_emergency_exception_buf(200)

class HR:
    def __init__(self):  
        self.i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
        self.oled = SSD1306_I2C(128, 64, self.i2c)
        self.sensor = ADC(Pin(26))
        self.button = Pin(12, Pin.IN, Pin.PULL_UP)
        
        self.samples_fifo = Fifo(750, 'H')
        self.filtered = array.array('H', [0] * 750)  #Create an 16 bit array filled with zeros
        self.write_index = 0  # Current position in circular buffer
        
        self.measuring = False    #checks are we actively measuring
        self.last_bpm = 0         
        self.button_flag = False  #when button pressed in ISR turns True
        self.peaks = array.array('I', [0] * 10)  # store up to 10 peak indexes
        self.peak_count = 0      
        self.last_display_update = 0 
        self.first_valid_bpm = False  
        
        self.timer = Piotimer(freq=250, mode=Piotimer.PERIODIC, callback=self.sample_isr)
        self.show_menu()
    
     
    # Display menu on the OLED
    def show_menu(self):
        self.oled.fill(0)
        self.oled.text("Measure HR", 20, 10)
        self.oled.text("Press to START", 5, 30)
        self.oled.show()
        
    # ISR (Interrupt service routine)    
    def sample_isr(self, timer):
        try:
            self.samples_fifo.put(self.sensor.read_u16()) # Store analog sensor to fifo buffer
        except RuntimeError:
            pass
        
        self.button_flag = not self.button.value() # Check button state (inverted because of  pull_up)
    
    # Process raw samples from fifo and move filtered buffer
    def process_samples(self):
        i = 0
        while self.samples_fifo.has_data() and i < 750:  #
            try:
                index = (self.write_index + i) % 750
                self.filtered[index] = self.samples_fifo.get() # Store filtered buffer from fifo
                i += 1
            except RuntimeError:
                break
            
        self.write_index = (self.write_index + i) % 750 # Update write_index to point to  the nest write posiion
        return i
                    
    
    # 3-point weighted moving average filter to reduce noise in the raw signal [1, 2, 1]. 
    def smooth_signal(self):
        for i in range(2, len(self.filtered)):
            self.filtered[i] = (self.filtered[i-2] +2 * self.filtered[i-1] +self.filtered[i]) // 4
    
    # Heart rate calculation from filtered signal
    def calculate_bpm(self):
        samples_processed = self.process_samples()
        if samples_processed == 0:
            return 0
        
        self.smooth_signal() # Apply smooth signal
        
        # Threshold calculation
        sorted_samples = sorted(self.filtered)  # Sort all filtered values
        low = sorted_samples[len(sorted_samples) // 10]     # Ignore lowest 10%
        high = sorted_samples[len(sorted_samples) * 9 // 10]   # Ignore highest 10%
        threshold = low + (high - low) * 7 // 10   # threshold = low + 60% of (high-low)
        
        # Peak detection
        self.peak_count = 0
        previous = self.filtered[0] # Previous sample value
        rising = False   
        
        for i in range(1, len(self.filtered)):
            current = self.filtered[i]   # Current sample value
            
            if current > threshold and previous <= threshold and rising: 
                if self.peak_count < len(self.peaks):
                    self.peaks[self.peak_count] = i  # store peak position
                    self.peak_count += 1
                rising = False
                
            elif current > previous:   # Rising edge detection
                rising = True
            previous = current      
        
        # Calculate bpm from intervals between peaks
        if self.peak_count >= 4:   # Need at least 4 peaks
            intervals = []   
            for j in range(1, self.peak_count):
                interval = self.peaks[j] - self.peaks[j-1] # distance between peaks in samples
                
                min_interval = int(60 / 260 * 250) # 160 bpm upper limit 
                max_interval = int(60 / 40 * 250)  # 40 bpm lower limit 
                if min_interval < interval < max_interval:  # Only accept valid range (40-160 bpm)
                    intervals.append(interval)
                
                if len(intervals) >= 3:
                    avg_interval = sum(intervals) // len(intervals)
                    return (60 * 250) // avg_interval      # BPM 
        return 0     
    
    # Main program loop
    def run(self):
        last_button_check = ticks_ms()
        bpm_history = array.array('I', [0] * 5) # Circular buffer to store past 5 BPM readings
        bpm_history_index = 0   
        
        while True:
            now = ticks_ms()
            if ticks_diff(now, last_button_check) > 300: #button handling (300ms debounce)
                last_button_check = now
                
                if self.button_flag:
                    self.button_flag = False  
                    self.measuring = not self.measuring
                    
                    if self.measuring:                
                        self.oled.fill(0)
                        self.oled.text("Measuring...", 0, 10)
                        self.oled.show()
                        self.last_display_update = 0   
                        self.first_valid_bpm = False        
                    else:
                        self.show_menu()
            
            if self.measuring:
                current_bpm = self.calculate_bpm()
                
                if current_bpm > 0:
                    bpm_history[bpm_history_index] = current_bpm   #if vald reading store in history buffer
                    bpm_history_index = (bpm_history_index + 1) % len(bpm_history)

                    if not self.first_valid_bpm:
                        self.first_valid_bpm = True
                    
                    if self.first_valid_bpm and ticks_diff(now, self.last_display_update) >= 3000: # update display every 5s after first valid
                        self.last_display_update = now
                        
                        bpm = sorted(bpm_history)[2] # Middle value of sorted array,median of last 5 readings 
                        self.oled.fill(0)
                        self.oled.text(f"BPM: {bpm}", 20, 10)
                        self.oled.text("Press to STOP", 5, 40)
                        self.oled.show()
                        print(f"{bpm} bpm")
                else:
                    if not self.first_valid_bpm:  
                        self.oled.fill(0)
                        self.oled.text("Measuring...", 0, 10)
                        self.oled.show()
            
            sleep(0.05)
        
hr = HR()
hr.run()
   