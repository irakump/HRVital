from oled import Encoder, Oled
from heart_rate import HR
import time
from basic_hrv_analysis_v2 import BasicHRVAnalysis
from menu import Menu

# Results for testing
#hrv_results = [77, 1000, 23, 22]
kubios_results = ['aikaleima', 77, 1000, 23, 22, -1.1, 1.9]
measurements = [['aikaleima', 55, 1000, 23, 22, 0.5, 1.8], ['aikaleima', 88, 999, 33, 54, 2.0, -1.5], [], []] # max pituus = 4!
#measurements = [] # test for no history

# Definitions
rot = Encoder()
oled = Oled()
hr = HR()
hrv = BasicHRVAnalysis()
menu = Menu(oled, rot, hr, hrv, measurements) # measurements-lista (kubios-mittauksesta!)

# TODO: hrv-mittauksen funktion sisään importaa rot (handler)
# history-logiikka ja paluu menuun
# oledista: stopping ja error texts näyttö, jos error tai hrv datan keräys epäonnistuu

# kaikki tiedostot pitää tallentaa picolle, jotta import toimii


# Start
#oled.logo()
oled.fill(0)
oled.main_menu()
oled.fill(0)

while True:
    value = menu.get_fifo_value()
    
    if value is not None:
        previous_selected_menu = oled.selected_menu
        print(f'previous menu: {previous_selected_menu}')
        
        menu.detect_user_action(value)
        oled.fill(0)
        
        if oled.selected_menu != previous_selected_menu:
            oled.selected_menu = menu.change_menu()
        else:
            menu.change_menu()
  
    
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
