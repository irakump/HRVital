import time
from oled import Encoder

# Menu logic
class Menu:
    def __init__(self, oled, rot, hr, hrv, measurements):
        self.oled = oled
        self.rot = rot
        self.hr = hr
        self.hrv = hrv
        self.measurements = measurements
    
    def make_new_rot_button(self):
        self.rot = Encoder()
        #self.mqtt = mqtt
        
    def get_fifo_value(self):
        if self.rot.fifo.has_data():
            fifo_value = self.rot.fifo.get()
            print(fifo_value)
            return fifo_value

        return None # return none, if fifo empty

    def detect_user_action(self, fifo_value):
        # read fifo value, update history index if history menu selected
        self.read_fifo_value(fifo_value)
        self.update_history_index(fifo_value)
        
        # set limits to menu and history indexes
        self.prevent_overscrolling()

        # update display
        if self.oled.selected_menu == 'main_menu':
            self.oled.main_menu()

        return self.oled.selected_menu

    def read_fifo_value(self, fifo_value):
        if fifo_value == 1:
            self.oled.selected_index += 1
        elif fifo_value == -1:
            self.oled.selected_index -= 1
        elif fifo_value == 0:  # rotary button pressed
            self.update_selected_menu()  # update the selected menu variable
            
    def update_history_index(self, fifo_value):
        if self.oled.selected_menu == 'history':
            if fifo_value == 1:
                self.oled.history_index += 1
            elif fifo_value == -1:
                self.oled.history_index -= 1
            
    def prevent_overscrolling(self):
        # Limit main menu indexes
        if self.oled.selected_menu == 'main_menu':
            self.oled.selected_index = min(3, max(0, self.oled.selected_index))
        
        # Limit history menu indexes
        elif self.oled.selected_menu == 'history':
            self.oled.history_index = min(len(self.measurements), max(0, self.oled.history_index))

        # Draw the selection symbol -> TARVITSEEKO TÄTÄ??
        #self.oled.text(self.oled.symbol, 5, self.oled.y + self.oled.line_height * self.oled.selected_index)

    def update_selected_menu(self):
        if self.oled.selected_menu == 'main_menu':
            
            if self.oled.selected_index == 0:
                self.oled.selected_menu = 'hr'
                
            elif self.oled.selected_index == 1:
                self.oled.selected_menu = 'hrv'
                
            elif self.oled.selected_index == 2:
                self.oled.selected_menu = 'kubios'
                
            elif self.oled.selected_index == 3:
                self.oled.selected_menu = 'history'
                self.oled.history_index = 0

    def run_selected_menu(self): # alkuperäinen
    #def run_selected_menu(self, rot): # uusi, testi       
        if self.oled.selected_menu == 'main_menu':
            self.oled.main_menu()

        elif self.oled.selected_menu == 'hr':
            self.run_hr()

        elif self.oled.selected_menu == 'hrv':
            self.run_hrv() # alkuperäinen
            #self.run_hrv(rot) # uusi

        elif self.oled.selected_menu == 'kubios':
            self.run_kubios() # ei valmis

        elif self.oled.selected_menu == 'history':
            self.run_history()
        
        return self.oled.selected_menu
    
    def run_hr(self):
        # Show the starting menu
        self.oled.start_measurement_menu()
        self.hr.reset_button()
        
        # Measure and show HR
        measurement_on = self.hr.run2()

        # Return to main menu when button pressed to stop measurement
        if not measurement_on:  # measurement_on == False
            self.oled.selected_menu = 'main_menu'

            self.rot.clear()  # clear the fifo
            self.hr.measuring = False

            self.oled.fill(0)
            self.oled.main_menu() # show the main menu
            time.sleep(0.1)
    
    # alkuperäinen (muuta nimet)
    def run_hrv1(self):
        # Show the starting menu
        self.oled.start_measurement_menu()
        self.wait_for_button_press()

        # Show collecting data text after the press
        self.oled.fill(0)
        self.oled.collecting_data() # update the oled
        self.oled.fill(0)
        
        # Collect data and analyse HRV
        hrv_results = self.hrv.get_basic_hrv_analysis()
        self.oled.hrv_data_collected()
        time.sleep(2) # Show data collected text for 2 sec
        self.oled.fill(0)

        # Show the results and return main menu after press
        self.oled.show_hrv_results(hrv_results)
        self.oled.selected_index = 0 # update select mark to top of the oled
        self.return_main_menu_after_button_press()
    
    ###### tästä alkaen lisätty uusi -> palaako menuun kesken mittauksen? ############
    def run_hrv(self):
        # Show the starting menu
        self.oled.start_measurement_menu()
        self.wait_for_button_press()

        # Show collecting data text after the press
        self.oled.fill(0)
        self.oled.collecting_data() # update the oled
        self.oled.fill(0)
        
        # Collect data and analyse HRV
        hrv_results = self.hrv.get_basic_hrv_analysis()
        
        # go back to main menu if hrv_results is None (no data, button pressed)
        if hrv_results is None:
            self.make_new_rot_button() # tee uusi rot nappi
            #self.oled.main_menu()
            self.back_to_main_menu()
            self.oled.main_menu()
        else:   
            self.oled.hrv_data_collected()
            time.sleep(2) # Show data collected text for 2 sec
            self.oled.fill(0)

            # Show the results and return main menu after press
            self.oled.show_hrv_results(hrv_results)
            self.oled.selected_index = 0 # update select mark to top of the oled
            self.make_new_rot_button() # lisätty
            self.return_main_menu_after_button_press()

        
        ###########################################
    
    def run_kubios(self): # KESKEN (ei vielä testattu, 1.5.)
        self.oled.start_measurement_menu()  # show the start menu
        self.wait_for_button_press()
        self.oled.collecting_data()
        
        # Collect HRV data
        all_ppis = self.hrv.get_basic_hrv_analysis() # funktion pitää palauttaa ppi:t!
        self.oled.hrv_data_collected()
        time.sleep(1.5) # show data collected -text for 1.5 sec
        self.oled.fill(0)
        self.oled.show_sending_data_text() # show sending data -text until Kubios is ready
        
        # Send data to Kubios and show result
        kubios_result = get_kubios_analysis_result(all_ppis)
        self.oled.fill(0)
        self.oled.show_kubios_result(kubios_result)
        self.oled.selected_index = 0
        self.return_main_menu_after_button_press() # go back to main menu

        #self.testi_kubios_tulos()
                        
    def run_history(self):
        in_history_menu = True
        
        while in_history_menu:
            button_value = self.get_fifo_value()
            
            # Continue loop and update OLED if fifo is empty
            if button_value is None:
                self.oled.fill(0)
                self.oled.history_menu(self.measurements)
                continue
            
            # Update OLED display to chosen history measurement
            self.detect_user_action(button_value) # update history index
            self.oled.fill(0) # lisätty
            self.oled.history_menu(self.measurements) # lisätty
            self.handle_history_selection(button_value)
                
            in_history_menu = False

    def is_button_pressed(self, button_value):
        if button_value == 0:
            return True
        else:
            return False

    def wait_for_button_press(self):  # wait for user to press the button
        while True:
            if self.rot.fifo.has_data():
                button_value = self.get_fifo_value()
                if self.is_button_pressed(button_value):
                    break

    def return_main_menu_after_button_press(self): # wait for button to be pressed, go to menu
        while True:
            if self.rot.fifo.has_data():
                button_value = self.get_fifo_value()
                
                if self.is_button_pressed(button_value):
                    self.oled.fill(0)
                    self.oled.selected_menu = 'main_menu'
                    self.oled.main_menu()  # go back to main menu
                    break
                
    def is_valid_history_index(self):
        # Check if history_index is in between 0 and len(self.measurements) - 1
        if self.oled.history_index < (len(self.measurements)):
            return True
        else:
            return False
        
    def show_selected_history(self):
        self.oled.fill(0)
        selected_measurement = self.measurements[self.oled.history_index]
        self.oled.show_kubios_results(selected_measurement)
        self.wait_for_button_press() # return to history menu after button is pressed
        
    def back_to_main_menu(self):
        self.oled.fill(0)
        self.oled.selected_index = 0
        self.oled.selected_menu = 'main_menu'
        time.sleep(0.1)
        
    def handle_history_selection(self, button_value):
        if self.is_button_pressed(button_value) and self.is_valid_history_index():
            self.show_selected_history() # show measurement
       
        elif self.is_button_pressed(button_value) and not self.is_valid_history_index():
            self.back_to_main_menu() # go back to main menu
