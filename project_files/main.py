from oled import Encoder, Oled
from heart_rate import HR
import time

# Rotary encoder and oled definitions
rot = Encoder()
oled = Oled()
hr = HR()

# kaikki tiedostot pitää tallentaa picolle, jotta import toimii

# Functions without a class
def evaluate_sns_pns(kubios_results):
    sns = kubios_results[4]
    pns = kubios_results[5]
    
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

def get_fifo_value(rot):   
    if rot.fifo.has_data():
        fifo_value = rot.fifo.get()
        print(fifo_value)
        return fifo_value
    
    return None # returns none, if fifo empty 


def detect_user_action(oled, fifo_value, measurements): # tarvitsee nyt parametrina listan kubios-mittauksista = measurements
    # read fifo value
    if fifo_value == 1:
        oled.selected_index += 1
    elif fifo_value == -1:
        oled.selected_index -= 1
    elif fifo_value == 0: # rotary button pressed
        if oled.selected_menu == 'main_menu' and oled.selected_index == 0:
            oled.selected_menu = 'hr'
        elif oled.selected_menu == 'main_menu' and oled.selected_index == 1:
            oled.selected_menu = 'hrv'
        elif oled.selected_menu == 'main_menu' and oled.selected_index == 2:
            oled.selected_menu = 'kubios'
        elif oled.selected_menu == 'main_menu' and oled.selected_index == 3:
            oled.selected_menu = 'history'
    
    # update history index
    if oled.selected_menu == 'history':
        if fifo_value == 1:
            oled.history_index += 1
        elif fifo_value == -1:
            oled.history_index -=1
    
    # prevent overscrolling
    if oled.selected_menu == 'main_menu':
        oled.selected_index = min(3, max(0, oled.selected_index))
    elif oled.selected_menu == 'history':
        oled.history_index = min(len(measurements), max(0, oled.history_index))
    
    oled.text(oled.symbol, 5, oled.y + oled.line_height * oled.selected_index) # draw the selection symbol
    
    # update display
    if oled.selected_menu == 'main_menu':
        oled.main_menu()

    return oled.selected_menu

def change_menu(oled, hr):
    if oled.selected_menu == 'main_menu':
        oled.main_menu()
        
    elif oled.selected_menu == 'hr':
        oled.hr_menu()
        hr.reset_button()
        running = hr.run2()
        
        if not running: # running == False, user pressed to stop measurement
            oled.selected_menu = 'main_menu'
            
            rot.clear() # clear the fifo
            
            hr.measuring = False
            
            oled.fill(0)
            oled.main_menu()
            time.sleep(0.1)
            
            return oled.selected_menu # return to main loop
            
    elif oled.selected_menu == 'hrv':
        # kutsu tässä hrv-datan mittauksen funktiota? Vai tämän funktion jälkeen pääohjelmassa?
        oled.collecting_data() # updates the oled (measures nothing)
        
    elif oled.selected_menu == 'kubios':
        # kutsu tässä hrv-datan mittauksen funktiota?
        oled.collecting_data()
        # lähetä tässä data kubiokseen?
        
    elif oled.selected_menu == 'history':
        oled.history_menu(measurements)

# Results for testing
hrv_results = [77, 1000, 23, 22]
kubios_results = [77, 1000, 23, 22, -1.1, 1.9]
measurements = [[55, 1000, 23, 22, 0.5, 1.8], [88, 999, 33, 54, 2.0, -1.5], [], []] # max pituus = 4!
#measurements = [] # test for no history

# Start
oled.logo()
oled.fill(0)
oled.main_menu()
oled.fill(0)

while True:
    
    value = get_fifo_value(rot)
    
    if value != None:
        previous_selected_menu = oled.selected_menu
        detect_user_action(oled, value, measurements)
        oled.fill(0)
        
        if oled.selected_menu != previous_selected_menu:
            oled.selected_menu = change_menu(oled, hr)
        else:
            change_menu(oled, hr)
    
    
    # TEST PRINTS below this row
    
    #oled.main_menu()
    
    #oled.collecting_data()
    #oled.hrv_data_collected()

    #oled.show_hrv_results(hrv_results)
    
    #oled.hr_menu()
    #oled.show_hr(99)
    
    #oled.stopping_message()
    #oled.error_message()

    #oled.show_kubios_results(kubios_results)
    
    #oled.history_menu(measurements)
    #oled.show_selected_history(measurements)
