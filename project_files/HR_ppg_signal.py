from time import ticks_ms, ticks_diff
from ssd1306 import SSD1306_I2C
from machine import Pin, I2C, ADC
from piotimer import Piotimer
from fifo import Fifo
import array
import micropython
micropython.alloc_emergency_exception_buf(200)

class HR:
    def __init__(self):
        # Hardware initialization
        self.i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
        self.oled = SSD1306_I2C(128, 64, self.i2c)
        self.sensor = ADC(Pin(26))
        self.button = Pin(12, Pin.IN, Pin.PULL_UP)

        # Buffers
        self.samples_fifo = Fifo(1500, 'H')  # ADC samples (1500 sample buffer), temporary store sample from ppg sensor (1500/250=6s)
        self.button_fifo = Fifo(50)          # Button press event queue, stores 50 button press
        
        self.filtered = array.array('H', [0]*750) #Circular buffer for filtered samples, creates an array of 750 element, each initialized to 0 
        self.write_index = 0              # Index to write the next sample in the (self.filtered[0],[1],[749]) # Overwrite old samples in a loop
        self.peaks = array.array('I', [0]*10) # Stores positions of detected peaks (max 10 peaks per detection cycle)
                                              # (array.array first one module name, and second is constructor) 
        
        # Display configuration
        self.width = 128
        self.height = 64
        self.ppg_buf = array.array('H', [0]*self.width) #Buffer for ppg signal values for display, initializes with 128 num of zeroes
        self.display_min = 30000  # Initial values PPG signal's low range
        self.display_max = 40000  # These are initial range for displaying the ppg signal
        
        # BPM calculation
        self.bpm_history = array.array('H', [0]*7) # Stores last 7 bpm for median filtering
        self.bpm_index = 0        # Store next bpm value in bpm_history
        self.display_bpm = 0      # BPM value shown on screen
        self.last_valid_bpm = 0   # Stores most recent valid bpm value 
        self.first_valid = False  # Indicate if any valid bpm has been measured
        
        # Timing control
        self.last_bpm_update = ticks_ms()  # Last bpm calculation
        self.last_ppg_update = ticks_ms()  # Last wave display update
        self.bpm_update_interval = 3000  # Minimum time between bpm calculation (ms)
        self.ppg_update_interval = 50    # Display refresh every 50ms
        
        # State flags
        self.measuring = False   # If measurment active
        self.last_button_check = ticks_ms()  # Last valid button press
        self.debounce_ms = 500    # Minimum time between button press (ms)
        
        # Initialize hardware
        self.timer = Piotimer(freq=250, mode=Piotimer.PERIODIC, callback=self.sample_isr)
        self.button.irq(handler=self.button_handler, trigger=Pin.IRQ_FALLING, hard=True)
        #self.show_menu() # poistettu


    # ISR called 250 times/second by hardware timer
    def sample_isr(self, timer):
        next_head = (self.samples_fifo.head + 1) % self.samples_fifo.size  # Calculate next write position
        if next_head != self.samples_fifo.tail:  # Only store sample if buffer isn't full (tail check prevents overflow)
            self.samples_fifo.put(self.sensor.read_u16())
   
   
    # Handles button presses
    def button_handler(self, pin):
        now = ticks_ms()
        if ticks_diff(now, self.last_button_check) > self.debounce_ms:
            self.last_button_check = now
            self.button_fifo.put(0)    # Stores a press event
    
    
    #Shows the start menu
    def show_menu(self):
        self.oled.fill(0)
        self.oled.text("Measure HR", 20, 10)
        self.oled.text("Press to START", 5, 30)
        self.oled.show()


    # Draws the heartbeat wave and BPM
    def draw_display(self, bpm):
        # Auto-scaling
        current_min = min(self.ppg_buf)
        current_max = max(self.ppg_buf)
        
        # Slowly adapt display range
        self.display_min = (self.display_min * 3 + current_min) // 4
        self.display_max = (self.display_max * 3 + current_max) // 4
        
        # Ensure minimum range 
        span = max(1000, self.display_max - self.display_min) # Picks either 1000 or diffrence, larger one 
        
        # Signal quality calculation (0-128 scale)
        quality = (current_max - current_min) // 100
        quality = min(128, max(0, quality))
        
         # Determine if signal is valid
        signal_valid = (quality > 10) and (quality < 120) 
        self.oled.fill(0)
        
        # Draw waveform 
        prev_y = None
        for x in reversed(range(self.width)):
            # Scale and invert (peaks go upward)
            y = 50 - int((self.ppg_buf[x] - self.display_min) * 30 / span) # scale signal to in the 30 pixel height range, the invert 
            y = max(10, min(60, y))  # keep y with screen boundaries (10 to 60)
            
            if prev_y is not None:
                self.oled.line(x+1, prev_y, x, y, 1) # Connect previous point to the current
            prev_y = y     # Store current y to connect next point
        
        # Display message based on signal quality
        if not signal_valid:
            self.oled.text("Invalid BPM", 0, 0)
        elif bpm > 0:
            self.oled.text(f"{bpm} BPM", 0, 0)
        else:
            self.oled.text("Place finger", 0, 0)
        
        # Draw signal quality indicator bar
        self.oled.rect(0, 10, quality, 3, 1)
        self.oled.show()
        
    
    # Moves samples from fifo to (self.filtered)
    def process_samples(self):
        count = 0     # counter to track how many samples are transferred in this cycle
        
        while self.samples_fifo.has_data() and count < 750:  # ensure don't write more than 750 samples (self.filtered) at once
            # calculate index in the (self.filtered), wrapping around at the end(749).
            # example: if write_index 748 and count 1 (748+1)%750=749 writes 749. (748+2)%750=0
            self.filtered[(self.write_index + count) % 750] = self.samples_fifo.get() 
            count += 1  # move to the next sample
        
        # update write_index to the new position after writing count samples
        self.write_index = (self.write_index + count) % 750  # example: if write_index 740 and count 20 (740+20)%750=10
    
    
    # Smooth the PPG signal using 3-point weighted moving average filter
    # weighted average:(25% i-2, 50% i-1, 25% current)//total weight
    def smooth_signal(self):
        for i in range(2, len(self.filtered)):     # Starts from index 2
            self.filtered[i] = (self.filtered[i-2] + 2*self.filtered[i-1] + self.filtered[i]) // 4 

    
    def calculate_bpm(self):
        # Signal quality thresholds for invalid signal
        current_min = min(self.filtered)
        current_max = max(self.filtered)
        quality = (current_max - current_min) // 100
        signal_valid = (quality > 10) and (quality < 120)
        
        if not signal_valid:  # If signal is not valid return 0,(no bpm)
            return 0
        
        self.smooth_signal()
        
        # Threshold calculation for peak detection (10th-90th percentile range to ignore extreme values)
        sorted_samples = sorted(self.filtered)  #Sort samples from low to high
        low = sorted_samples[len(sorted_samples)//10]  # ignore lowest 10%,
        high = sorted_samples[len(sorted_samples)*9//10]  # ignore highest 10%
        threshold = low + (high-low) * 8 // 10 

        # Peak detection with rising edge logic
        self.peak_count = 0      # reset counter for peak found
        prev = self.filtered[0]  # store first sample for comaparison
        rising = False
        last_peak = -1000   # initialize with impossible value to ensure first peak is accepted

        for i in range(1, len(self.filtered)): 
            curr = self.filtered[i]    # current ppg sample
            
            if curr > threshold and prev <= threshold and rising: # Detect when signal crosses threshold during rising phase
                if (i - last_peak) > 125:  # Minimum 126 samples between peaks at 250Hz. calculation:(60s*250samples/s)/240beats = 62.5 samples/beats 
                    
                    if self.peak_count < len(self.peaks):  # if there is space in self.peak array add current peak there
                        self.peaks[self.peak_count] = i  
                        self.peak_count += 1  # Update last peak position
                        last_peak = i       # reset for next rising edge
                        
                rising = False
            elif curr > prev:
                rising = True  
            prev = curr 

        # Calculate BPM from valid intervals (30-240 BPM)
        if self.peak_count >= 4:      # Require at least 4 peaks
            intervals = []
            
            # Calculate time between all consecutive peaks
            for j in range(1, self.peak_count):
                interval = self.peaks[j] - self.peaks[j-1]  # Sample between peaks
                
                # 30-240 BPM
                if 62 < interval < 500:  # 240 bpm = 62.5 samplles (60*250/240), #30 bpm = 500 samples (60*250/30 = 500)
                    intervals.append(interval)
                    
            # Require at least 3 intervals
            if len(intervals) >= 3:
                median_interval = sorted(intervals)[len(intervals)//2]  # Median interval for stable BPM
                return (60 * 250) // median_interval  # Convert samples to BPM

        return 0

############################################
    # Main program loop, original
    def run1(self):
        while True:
            # Handle button press
            while self.button_fifo.has_data():
                _ = self.button_fifo.get()
                self.measuring = not self.measuring
                
                if not self.measuring:   # Stop measurment mode
                    self.show_menu()
                else:
                    # Resets all bpm value
                    self.first_valid = False
                    self.bpm_index = 0
                    self.last_bpm_update = ticks_ms()
                    
                    for i in range(len(self.bpm_history)):  # Clear BPM history
                        self.bpm_history[i] = 0
                        
                    self.oled.fill(0)
                    self.oled.text("Measuring...", 20, 30)
                    self.oled.show()

            if self.measuring:
                # Process available samples
                self.process_samples()
                
                # Update BPM 
                now = ticks_ms()
                if ticks_diff(now, self.last_bpm_update) >= self.bpm_update_interval:  # Calculate bpm fixed intervals
                    self.last_bpm_update = now  # reset timer
                    current_bpm = self.calculate_bpm()
                    
                    if current_bpm > 0:   # store valid bpm
                        self.bpm_history[self.bpm_index] = current_bpm   # Save bpm history buffer
                        self.bpm_index = (self.bpm_index + 1) % len(self.bpm_history) # Move index forward with wraparound
                        self.first_valid = True
                        self.last_valid_bpm = current_bpm  
                        
                        # Only update display BPM if we have 3 valid readings
                        valid = sorted([b for b in self.bpm_history if b > 0]) # Filter out invalid bpm(0) and sort the remaining values.
                        if len(valid) >= 3:
                            self.display_bpm = valid[len(valid)//2]  # Take the middle valid bpm after sorting
                
                # Update waveform display every 50ms
                if ticks_diff(now, self.last_ppg_update) >= self.ppg_update_interval:
                    self.last_ppg_update = now
                    
                    # Get most recent samples for display (continuous sampling)
                    for i in range(self.width):
                        # calculate which sample to display at pixel
                        index = (self.write_index - (self.width - i)*5) % 750 # (self.width - i)*5 = spaces samples 5 positions apart, %750 wrap around 
                        self.ppg_buf[i] = self.filtered[index]   # Stores the sample value for display
                    
                    self.draw_display(self.display_bpm)  # Update oled with current bpm and waveform

################
# uusi main loop
    def run(self):
        self.show_menu() # lisätty
        while True:
            # Handle button press
            while self.button_fifo.has_data():
                _ = self.button_fifo.get()
                self.measuring = not self.measuring
                
                if not self.measuring:   # Stop measurment mode
                    return False # lisätty # exit back to menu
                    #self.show_menu()
                else:
                    # Resets all bpm value
                    self.first_valid = False
                    self.bpm_index = 0
                    self.last_bpm_update = ticks_ms()
                    
                    for i in range(len(self.bpm_history)):  # Clear BPM history
                        self.bpm_history[i] = 0
                        
                    self.oled.fill(0)
                    self.oled.text("Measuring...", 20, 30)
                    self.oled.show()

            if self.measuring:
                # Process available samples
                self.process_samples()
                
                # Update BPM 
                now = ticks_ms()
                if ticks_diff(now, self.last_bpm_update) >= self.bpm_update_interval:  # Calculate bpm fixed intervals
                    self.last_bpm_update = now  # reset timer
                    current_bpm = self.calculate_bpm()
                    
                    if current_bpm > 0:   # store valid bpm
                        self.bpm_history[self.bpm_index] = current_bpm   # Save bpm history buffer
                        self.bpm_index = (self.bpm_index + 1) % len(self.bpm_history) # Move index forward with wraparound
                        self.first_valid = True
                        self.last_valid_bpm = current_bpm  
                        
                        # Only update display BPM if we have 3 valid readings
                        valid = sorted([b for b in self.bpm_history if b > 0]) # Filter out invalid bpm(0) and sort the remaining values.
                        if len(valid) >= 3:
                            self.display_bpm = valid[len(valid)//2]  # Take the middle valid bpm after sorting
                
                # Update waveform display every 50ms
                if ticks_diff(now, self.last_ppg_update) >= self.ppg_update_interval:
                    self.last_ppg_update = now
                    
                    # Get most recent samples for display (continuous sampling)
                    for i in range(self.width):
                        # calculate which sample to display at pixel
                        index = (self.write_index - (self.width - i)*5) % 750 # (self.width - i)*5 = spaces samples 5 positions apart, %750 wrap around 
                        self.ppg_buf[i] = self.filtered[index]   # Stores the sample value for display
                    
                    self.draw_display(self.display_bpm)  # Update oled with current bpm and waveform



#hr = HR()
#hr.run()
