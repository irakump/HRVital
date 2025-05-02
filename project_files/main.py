from oled import Encoder, Oled
from HR_ppg_signal import HR
import time
from basic_hrv_analysis import BasicHRVAnalysis
from menu import Menu
from kubios import Kubios
from history import History

# Definitions
hr = HR()
rot = Encoder()
oled = Oled()
hrv = BasicHRVAnalysis()
kubios = Kubios()
history = History()
menu = Menu(oled, rot, hr, hrv, kubios, history)

# Start
oled.logo()
oled.fill(0)
oled.main_menu()
oled.fill(0)

# Main loop
while True:
    button_value = menu.get_fifo_value()
    
    if button_value is not None:
        menu.detect_user_action(button_value)
        oled.fill(0)

        menu.run_selected_menu()
