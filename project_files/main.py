from oled import Encoder, Oled

# kaikki tiedostot pitää tallentaa picolle, jotta import toimii

# Results for testing
hrv_results = [77, 1000, 23, 22]
kubios_results = [77, 1000, 23, 22, -1.1, 1.9]
#measurements = [[55, 1000, 23, 22, 0.5, 1.8], [88, 999, 33, 54, 2.0, -1.5], [], []] # max pituus = 4!
measurements = [] # test for no history

# Start
oled.main_menu()
oled.fill(0)

while True:
    
    value = get_fifo_value(rot)
    
    if value != None:
        detect_user_action(oled, value, measurements)
        oled.fill(0)
        change_menu(oled)
    
    
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
