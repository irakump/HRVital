from oled import Encoder, Oled
from heart_rate import HR
import time
from basic_hrv_analysis import BasicHRVAnalysis
from menu import Menu

# Results for testing
#hrv_results = [77, 1000, 23, 22]
kubios_result = ['aikaleima', 77, 1000, 23, 22, -1.1, 1.9]
measurements = [['aikaleima', 55, 1000, 23, 22, 0.5, 1.8], ['aikaleima', 88, 999, 33, 54, 2.0, -1.5], ['aikaleima', 72, 878, 29, 51, 1.0, -1.1]] # max pituus = 4!
#measurements = [] # test for no history

# Definitions
rot = Encoder()
oled = Oled()
hr = HR()
hrv = BasicHRVAnalysis()
menu = Menu(oled, rot, hr, hrv, measurements) # measurements-lista (kubios-mittauksesta!)

# TODO: hrv-mittauksen funktion sisään importaa rot (handler)
# oledista: stopping ja error texts näyttö, jos error tai hrv datan keräys epäonnistuu

# kaikki tiedostot pitää tallentaa picolle, jotta import toimii


# Start
#oled.logo()
oled.fill(0)
oled.main_menu()
oled.fill(0)

# Main loop
while True:
    button_value = menu.get_fifo_value()
    
    if button_value is not None:
        menu.detect_user_action(button_value)
        oled.fill(0)
        
        # to compare values (may not be necessary)
        #previous_menu = oled.selected_menu
        #new_menu = menu.run_selected_menu()

        menu.run_selected_menu()
        
    
    # TEST PRINTS below this row
    
    #oled.main_menu()
    
    #oled.collecting_data()
    #oled.hrv_data_collected()

    #oled.show_hrv_results(hrv_results)
    
    #oled.start_measurement_menu()
    #oled.show_hr(99)
    
    #oled.stopping_message()
    #oled.error_message()

    #oled.show_kubios_results(kubios_result)
    
#oled.history_menu(measurements)
#oled.show_selected_history(measurements)
