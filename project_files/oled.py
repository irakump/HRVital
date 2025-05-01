import time
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
from fifo import Fifo
from led import Led
import micropython 
micropython.alloc_emergency_exception_buf(200)

class Encoder:
    def __init__(self):
        self.a = Pin(10, mode = Pin.IN, pull = Pin.PULL_UP)
        self.b = Pin(11, mode = Pin.IN, pull = Pin.PULL_UP)
        self.a.irq(handler = self.scroll_handler, trigger = Pin.IRQ_RISING, hard = True)
        
        self.button = Pin(12, Pin.IN, Pin.PULL_UP)
        self.button.irq(handler = self.button_handler, trigger = Pin.IRQ_RISING, hard = True)
        self.previous_button_press_timestamp = 0
        
        self.fifo = Fifo(30, typecode = 'i')
        
    def scroll_handler(self, pin):
        if self.b():
            self.fifo.put(-1)
        else:
            self.fifo.put(1)
    
    def button_handler(self, button):
        current_timestamp = time.ticks_ms()
        # ignore button press if less than 300 ms from previous
        if time.ticks_diff(current_timestamp, self.previous_button_press_timestamp) > 300:
            self.fifo.put(0)
            self.previous_button_press_timestamp = current_timestamp
        else:
            self.fifo.put(-2)
            
    def clear(self): # clear the fifo
        while self.fifo.has_data():
            x = self.fifo.get()

class Oled:
    def __init__(self):
        self.i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
        self.oled_width = 128
        self.oled_height = 64
        self.oled = SSD1306_I2C(self.oled_width, self.oled_height, self.i2c)

        # Menu settings
        self.x = 20
        self.y = 5
        self.line_height = 15 # use when 4 rows in the menu
        self.symbol = '>'
        self.selected_index = 0 # initial value
        self.history_index = 0
        self.selected_menu = 'main_menu' # initial value
        self.menu_shown = False
        
        # Text settings
        self.start_measurement_texts = ['Touch the sensor', '   and press', '   to START']
        self.stop_text = '(Press to stop)'
        self.data_collection_texts = ['  Collecting', '    data...', ' Wait for 30 s']
        self.data_collected_texts = ['Data collected', '', '  Displaying', '  results...']
        self.sending_data_texts = ['', 'Sending', 'data...']
        self.hrv_items = ['Avg HR: ', 'Avg PPI: ', 'RMSSD: ', 'SDNN: ']
        sns_index = 'normal'  # initial value
        pns_index = 'normal'
        self.hrv_units = ['BPM', 'ms', 'ms', 'ms']
        self.kubios_items = ['', 'Avg HR: ', 'Avg PPI: ', 'RMSSD: ', 'SDNN: ', 'SNS: ', 'PNS: ']
        self.kubios_units = ['', 'BPM', 'ms', 'ms', 'ms', sns_index, pns_index]
        self.stopping_text = ['Returning main', 'menu in 5 s...', '', 'Press to return']
        self.error_text = ['  DATA ERROR', 'Press to retry', '', 'Menu in 5 s...']

    def fill(self, colour):
        self.oled.fill(colour)
        
    def show(self):
        self.oled.show()
        
    def text(self, text, x, y):
        self.oled.text(text, x, y)
    
    def main_menu(self):
        self.menu = ['Measure HR', 'HRV analysis', 'Kubios', 'History']
        
        # display menu items
        for item in self.menu:
            self.index = self.menu.index(item)  # index of menu item in menu list
            self.text(item, self.x, self.y + self.line_height * self.index)
        
        self.text(self.symbol, 5, self.y + self.line_height * self.selected_index) # draw the selection symbol
        self.show() # update display
    
    def logo(self):
        self.text('HRVital', 37, 20)
        self.show()
        time.sleep(3)
    
    # HR
    def start_measurement_menu(self):
        for item in self.start_measurement_texts:
            index = self.start_measurement_texts.index(item)
            self.text(item, 3, 14 + self.line_height * index)
        
        #self.text(self.stop_text, 5, self.y + self.line_height * (index + 1))
        self.show()

    # tähän luetaan mitattu bpm-arvo fifosta!
    def show_hr(self, bpm_value):
        self.text(f'{bpm_value} BPM', self.x * 2, self.y + self.line_height * 1)
        self.text(self.stop_text, 5, self.y + self.line_height * 3)
        self.show()
    
    # HRV
    def collecting_data(self): # käytä samaa myös Kubiokseen
        for item in self.data_collection_texts:
            index = self.data_collection_texts.index(item)
            self.text(item, 5, self.y + self.line_height * index)
        self.text(self.stop_text, 5, self.y + self.line_height * (index + 1))

        self.show()
    
    def hrv_data_collected(self): # sama viesti myös Kubios-valinnan jälkeen
        for item in self.data_collected_texts:
            index = self.data_collected_texts.index(item)
            self.text(item, 5, self.y + self.line_height * index)
            
        self.show()
    
    def show_sending_data_text(self):
        for item in self.sending_data_texts:
            index = self.sending_data_texts.index(item)
            self.text(item, 33, self.y + self.line_height * index)
        
        self.show()
        
    def show_hrv_results(self, hrv_results):
        for item in self.hrv_items:
            index = self.hrv_items.index(item)
            text = f'{item}{hrv_results[index]} {self.hrv_units[index]}'
            self.text(text, 0, self.y + self.line_height * index)
        
        self.show()
    
    # Kubios
    def show_kubios_results(self, kubios_result):
        sns_pns = evaluate_sns_pns(kubios_result) # get sns and pns index value
        sns_index = sns_pns[0]
        pns_index = sns_pns[1]
        
        # update indexed to the units list
        self.kubios_units[4] = sns_index
        self.kubios_units[5] = pns_index
        
        for item in self.kubios_items:
            index = self.kubios_items.index(item)
            print(f'kubios items -listan indeksi: {index}')
            #text = f'{item}{self.measurements[index]} {self.kubios_units[index]}' # versio 1
            text = f'{item}{kubios_result[index]} {self.kubios_units[index]}'
            self.text(text, 0, self.y + 8 * index)
        
        self.show()
    
    # History
    def history_menu(self, measurements): # parametrina Kubios-mittauksen tuloksia listassa: [[],[],[]] -> listoja listan sisällä?
        for i in range(len(measurements)):
            text = f'Measurement {i + 1}'
            self.text(text, self.x, self.y + 12 * i) # max 4 mittausta näkyvissä + menu palaaminen
        
        if len(measurements) == 0:
            self.text('NO HISTORY', self.x, self.y + 20)
        
        self.text('Main menu', self.x, self.y + 12 * len(measurements))
        
        self.text(self.symbol, 5, self.y + 12 * self.history_index) # draw the selection symbol
        self.show()
    
    def show_selected_history(self, measurements):
        index = self.history_index
        selected_measurement = measurements[index]
        
        self.show_kubios_results(selected_measurement)

    # Stop and error
    def stopping_message(self):
        for item in self.stopping_text:
           index = self.stopping_text.index(item)
           self.text(item, 6, self.y + self.line_height * index)
    
        self.show()    

    def error_message(self):
        for item in self.error_text:
           index = self.error_text.index(item)
           self.text(item, 8, self.y + self.line_height * index)
    
        self.show()

def evaluate_sns_pns(kubios_result):
    sns = kubios_result[4]
    pns = kubios_result[5]
    
    # sns
    if sns < -1:
        sns_index = 'low'
    elif -1 <= sns < 1:
        sns_index = 'normal'
    else:
        sns_index = 'high'
    
    # pns
    if pns < -1:
        pns_index = 'low'
    elif -1 <= pns < 1:
        pns_index = 'normal'
    else:
        pns_index = 'high'        
    
    return sns_index, pns_index

# Results for testing
hrv_results = [77, 1000, 23, 22]
kubios_result = ['aikaleima', 77, 1000, 23, 22, -1.1, 1.9]
#measurements = [[55, 1000, 23, 22, 0.5, 1.8], [88, 999, 33, 54, 2.0, -1.5], [], []] # max pituus = 4!
#measurements = [] # test for no history
