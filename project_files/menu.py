import time
from oled import Encoder
from HR_ppg_signal import HR

# Menu logic
class Menu:
    def __init__(self, oled, rot, hr, hrv, kubios, history):
        self.oled = oled
        self.rot = rot
        self.hr = hr
        self.hrv = hrv
        self.kubios = kubios
        self.history = history
    
    def make_new_rot_button(self):
        self.rot = Encoder()
    
    def make_new_hr_button(self):
        self.hr = HR()
        
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
            self.oled.history_index = min(len(self.history.read_from_history_file()), max(0, self.oled.history_index))

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

    def run_selected_menu(self):     
        if self.oled.selected_menu == 'main_menu':
            self.oled.main_menu()

        elif self.oled.selected_menu == 'hr':
            self.run_hr()

        elif self.oled.selected_menu == 'hrv':
            self.run_hrv()

        elif self.oled.selected_menu == 'kubios':
            self.run_kubios() # ei valmis

        elif self.oled.selected_menu == 'history':
            self.run_history()
        
        return self.oled.selected_menu

######## tästä alkaa uusi versio, hr
    def run_hr(self):
        # tyhjennä tässä hr-button? vai hr-funktiossa?
        self.make_new_hr_button()
        #self.hr.show_menu() # näyttää valikon; onko tarpeellinen?
        measuring = self.hr.run()
        if not measuring: # arvo on False
            # tyhjennä hr-buttonin fifo
            try:
                self.hr.button_fifo.clear()
            except:
                pass
            """
            #tyhjennä rot fifo
            try:
                self.rot.clear()
            except:
                pass"""
            
            time.sleep(0.2) # vai 0.1?
            
            # ONGELMA: palaa menuun, mutta pitää liikuttaa rotarya jotta se rekisteröi
            # pitääkö back to main menussa päivittää näyttö?
            
            print(f'measuring arvo: {measuring}')
            #self.make_new_rot_button() # ei toimi tässä
            #self.rot.clear() # tyhjennä fifo # ei ehkä toimi/tarvi
            self.back_to_main_menu() # tyhjennä rot-fifo, palaa main menuun
            
            # voiko tässä käydä että se olettaa painalluksen tarkoittavan siirtymistä
            # ..hr-menuun??

    # alkuperäinen versio, nimi oli run_hr
    def run_hr2(self):
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
#####################

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
        
        # Go back to main menu if hrv_results is None (button pressed)
        if hrv_results is None:
            self.make_new_rot_button() # new rot button
            self.show_returning_message()
            
            # Go back to main menu
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

    
    def run_kubios(self):
        self.oled.start_measurement_menu()  # show the start menu
        self.wait_for_button_press()
        self.oled.fill(0)
        self.oled.collecting_data()
        
        # Send data to Kubios and show result
        kubios_result = self.kubios.analyze_data_with_kubios()
        print(kubios_result)
        
        # show message if kubios result is a string
        if isinstance(kubios_result, str):
            self.make_new_rot_button() # new rot button
            #self.show_returning_message()
            self.oled.fill(0)
            #self.oled.text("Unable", 30, 20)
            self.oled.text(kubios_result, 30, 20)
            self.oled.show()
            time.sleep(2)  # show result for 2s
            
            # Go back to main menu
            self.back_to_main_menu()
            self.oled.main_menu()
        
        # print kubios result to screen
        else:
            self.oled.fill(0)
            self.oled.show_kubios_results(kubios_result)
            self.oled.selected_index = 0
        
            # Go back to main menu
            self.make_new_rot_button() # new rot button
            self.return_main_menu_after_button_press() # go back to main menu

                        
    def run_history(self):
        in_history_menu = True
        
        while in_history_menu:
            button_value = self.get_fifo_value()
            
            # Continue loop and update OLED if fifo is empty
            if button_value is None:
                self.oled.fill(0)
                self.oled.history_menu(self.history.read_from_history_file())
                continue
            
            # Update OLED display to chosen history measurement
            self.detect_user_action(button_value) # update history index
            self.oled.fill(0) # lisätty
            self.oled.history_menu(self.history.read_from_history_file()) # lisätty
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
        if self.oled.history_index < (len(self.history.read_from_history_file())):
            return True
        else:
            return False
        
    def show_selected_history(self):
        self.oled.fill(0)
        all_history_measurements = self.history.read_from_history_file()
        #print(all_history_measurements)
        
        #print(all_history_measurements.get(str(self.oled.history_index)))
        
        selected_measurement = all_history_measurements.get(str(self.oled.history_index))
        self.oled.show_kubios_results(selected_measurement)
        self.wait_for_button_press() # return to history menu after button is pressed
        
    def back_to_main_menu(self):
        self.rot.clear() # lisätty -> vanhan fifon tyhjennys
        self.make_new_rot_button() # lisätty (kun palaa hr-mittauksesta menuun, tarvii napin)
        self.oled.fill(0)
        self.oled.selected_index = 0
        self.oled.selected_menu = 'main_menu'
        
        # tämä lisätty hr-funktiota varten (rikkooko muualta jotakin?)
        self.oled.main_menu() # return to main menu and show
        
        time.sleep(0.1)
        
    def handle_history_selection(self, button_value):
        if self.is_button_pressed(button_value) and self.is_valid_history_index():
            self.show_selected_history() # show measurement
       
        elif self.is_button_pressed(button_value) and not self.is_valid_history_index():
            # Go back to main menu
            self.back_to_main_menu()
            time.sleep(0.1)
            self.oled.main_menu()
    
    def show_returning_message(self):
        self.oled.fill(0)
        self.oled.text('Returning...', 22, 20)
        self.oled.show()
        time.sleep(2)
        self.oled.fill(0)
