# old main.py file
from oled import Encoder, Oled
from heart_rate import HR
import time
from basic_hrv_analysis_v2 import BasicHRVAnalysis

# Definitions
rot = Encoder()
oled = Oled()
hr = HR()
hrv = BasicHRVAnalysis()

# TODO: hrv-mittauksen funktion sisään importaa rot (handler)

# kaikki tiedostot pitää tallentaa picolle, jotta import toimii

# Functions without a class

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
        update_selected_menu() # update the selected menu variable
        
        if oled.selected_menu == 'hrv': # tarviiko tätä? on jo funktio change
            pass
            # TODO: kun painaa nappia kesken mittauksen tai tulosten jälkeen, palaa menuun
             
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

def update_selected_menu():
    if oled.selected_menu == 'main_menu':
        if oled.selected_index == 0:
            oled.selected_menu = 'hr'
        elif oled.selected_index == 1:
            oled.selected_menu = 'hrv'
        elif oled.selected_index == 2:
            oled.selected_menu = 'kubios'
        elif oled.selected_index == 3:
            oled.selected_menu = 'history'

def change_menu(oled, hr):
    if oled.selected_menu == 'main_menu':
        oled.main_menu()
        
    elif oled.selected_menu == 'hr':
        oled.start_measurement_menu()
        hr.reset_button()
        measurement_on = hr.run2()
        
        if not measurement_on: # measurement_on == False, user pressed to stop measurement
            oled.selected_menu = 'main_menu'
            
            rot.clear() # clear the fifo
            hr.measuring = False
            
            oled.fill(0)
            oled.main_menu()
            time.sleep(0.1)
            
            return oled.selected_menu # return to main loop
            
    elif oled.selected_menu == 'hrv':
        oled.start_measurement_menu() # show the start menu
        wait_for_button_press()
        
        # HRV measurement after the press
        oled.fill(0)
        oled.collecting_data() # update the oled
        oled.fill(0)
        hrv_results = hrv.get_basic_hrv_analysis() # collect data and analyse
        oled.hrv_data_collected()
        time.sleep(2.5)
        oled.fill(0)
        
        oled.show_hrv_results(hrv_results) # show results
        return_main_menu_after_button_press() # return main menu
        return oled.selected_menu
        
    elif oled.selected_menu == 'kubios':
        oled.start_measurement_menu() # show the start menu
        wait_for_button_press()
        
        oled.collecting_data()
        # kutsu tässä hrv-datan mittauksen funktiota
        
        #oled.hrv_data_collected() -> näytä kun mittaus valmis
        # lähetä tässä data kubiokseen?
        return oled.selected_menu
        
    elif oled.selected_menu == 'history':
        oled.history_menu(measurements)
        # TODO: logiikka valinnalle (ks. main menun logiikka)
        # rivien lkm riippuu measurements-listan koosta (max 4)
            # -> indeksien mukaan mittauksen valinta? indeksi 0 -> measurements[0]?
        # detect_user_action-funktiossa on history_index
        
        # tests, not working
        #value = get_fifo_value(rot)
        #detect_user_action(oled, value, measurements)
        #oled.text(oled.symbol, 5, oled.y + oled.line_height * oled.history_index)
        return oled.selected_menu

def wait_for_button_press(): # wait for user to press the button
    while True:
        if rot.fifo.has_data():
            value = get_fifo_value(rot)
            if value == 0:
                break

def return_main_menu_after_button_press(): # wait for button to be pressed, return menu
    while True:
        if rot.fifo.has_data():
            value = get_fifo_value(rot)
            if value == 0: # button press
                oled.fill(0)
                oled.selected_menu = 'main_menu'
                oled.main_menu() # return to main menu
                break

# Results for testing
#hrv_results = [77, 1000, 23, 22]
kubios_results = ['aikaleima', 77, 1000, 23, 22, -1.1, 1.9]
measurements = [['aikaleima', 55, 1000, 23, 22, 0.5, 1.8], ['aikaleima', 88, 999, 33, 54, 2.0, -1.5], [], []] # max pituus = 4!
#measurements = [] # test for no history


# Start
#oled.logo()
oled.fill(0)
oled.main_menu()
oled.fill(0)

while True:
    value = get_fifo_value(rot)
    
    if value is not None:
        previous_selected_menu = oled.selected_menu
        print(f'previous menu: {previous_selected_menu}')
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
    
    #oled.start_measurement_menu()
    #oled.show_hr(99)
    
    #oled.stopping_message()
    #oled.error_message()

    #oled.show_kubios_results(kubios_results)
    
#oled.history_menu(measurements)
#oled.show_selected_history(measurements)
