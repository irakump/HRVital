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

        return None # Return none, if fifo empty

    def detect_user_action(self, fifo_value):
        # Read fifo value, update history index if history menu selected
        self.read_fifo_value(fifo_value)
        self.update_history_index(fifo_value)
        
        # Set limits to menu and history indexes
        self.prevent_overscrolling()

        # Update display
        if self.oled.selected_menu == 'main_menu':
            self.oled.main_menu()

        return self.oled.selected_menu

    def read_fifo_value(self, fifo_value):
        if fifo_value == 1:
            self.oled.selected_index += 1
        elif fifo_value == -1:
            self.oled.selected_index -= 1
        elif fifo_value == 0:  # Rotary button pressed
            self.update_selected_menu()  # Update the selected menu variable
            
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
            self.run_kubios()

        elif self.oled.selected_menu == 'history':
            self.run_history()
        
        return self.oled.selected_menu

    def run_hr(self):
        # Set new HR-button
        self.make_new_hr_button()
        
        # Measure
        measuring = self.hr.run()
        if not measuring: # Measuring returns False (user pressed button)
            
            # Clear HR-fifo
            try:
                self.hr.button_fifo.clear()
            except:
                pass
            
            time.sleep(0.2)
            
            # Go back to main menu (clear rot-fifo)
            self.back_to_main_menu()
            
    def run_hrv(self):
        # Show starting menu
        self.oled.start_measurement_menu()
        self.wait_for_button_press()

        # Show collecting data text after the press
        self.oled.fill(0)
        self.oled.collecting_data() # Update the oled
        self.oled.fill(0)
        
        # Collect data and analyse HRV
        hrv_results = self.hrv.get_basic_hrv_analysis()
        
        # Go back to main menu if hrv_results is None (button pressed)
        if hrv_results is None:
            self.make_new_rot_button() # New rot button
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
            self.oled.selected_index = 0 # Update select mark to top of the oled
            self.make_new_rot_button()
            self.return_main_menu_after_button_press()

    def run_kubios(self):
        self.oled.start_measurement_menu() # Show the start menu
        self.wait_for_button_press()
        self.oled.fill(0)
        self.oled.collecting_data()
        
        # Send data to Kubios and show result
        kubios_result = self.kubios.analyze_data_with_kubios()
        print(kubios_result)
        
        # Show message if kubios result is a string
        if isinstance(kubios_result, str):
            self.make_new_rot_button() # New rot button
            self.oled.fill(0)
            self.oled.text(kubios_result, 30, 20)
            self.oled.show()
            time.sleep(2)  # Show result for 2 s
            
            # Go back to main menu
            self.back_to_main_menu()
            self.oled.main_menu()
        
        # Print kubios result to screen
        else:
            self.oled.fill(0)
            self.oled.show_kubios_results(kubios_result)
            self.oled.selected_index = 0
        
            # Go back to main menu
            self.make_new_rot_button() # New rot button
            self.return_main_menu_after_button_press() # Go back to main menu
                  
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
            self.detect_user_action(button_value) # Update history index
            self.oled.fill(0)
            self.oled.history_menu(self.history.read_from_history_file())
            self.handle_history_selection(button_value)
                
            in_history_menu = False

    def is_button_pressed(self, button_value):
        if button_value == 0:
            return True
        else:
            return False

    def wait_for_button_press(self):  # Wait for user to press the button
        while True:
            if self.rot.fifo.has_data():
                button_value = self.get_fifo_value()
                if self.is_button_pressed(button_value):
                    break

    def return_main_menu_after_button_press(self): # Wait for button to be pressed, go to menu
        while True:
            if self.rot.fifo.has_data():
                button_value = self.get_fifo_value()
                
                if self.is_button_pressed(button_value):
                    self.oled.fill(0)
                    self.oled.selected_menu = 'main_menu'
                    self.oled.main_menu()  # Go back to main menu
                    break
                
    def is_valid_history_index(self):
        # Check if history_index is in between 0 and len(list) - 1
        if self.oled.history_index < (len(self.history.read_from_history_file())):
            return True
        else:
            return False
        
    def show_selected_history(self):
        self.oled.fill(0)
        all_history_measurements = self.history.read_from_history_file()
        
        selected_measurement = all_history_measurements.get(str(self.oled.history_index))
        self.oled.show_kubios_results(selected_measurement)
        self.wait_for_button_press() # Return to history menu after button is pressed
        
    def back_to_main_menu(self):
        self.rot.clear() # Clear fifo
        self.make_new_rot_button() # Set new button
        self.oled.fill(0)
        self.oled.selected_index = 0
        self.oled.selected_menu = 'main_menu'
        self.oled.main_menu() # Return to main menu and update oled
        time.sleep(0.1)
        
    def handle_history_selection(self, button_value):
        if self.is_button_pressed(button_value) and self.is_valid_history_index():
            self.show_selected_history() # Show measurement
       
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
