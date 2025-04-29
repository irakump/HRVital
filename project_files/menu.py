import time

# Menu logic
class Menu:
    def __init__(self, oled, rot, hr, hrv, measurements):
        self.oled = oled
        self.rot = rot
        self.hr = hr
        self.hrv = hrv
        self.measurements = measurements
        
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
            print(f'history index: {self.oled.history_index}')
            
    def prevent_overscrolling(self):
        # Limit main menu indexes
        if self.oled.selected_menu == 'main_menu':
            self.oled.selected_index = min(3, max(0, self.oled.selected_index))
        
        # Limit history menu indexes
        elif self.oled.selected_menu == 'history':
            self.oled.history_index = min(len(self.measurements), max(0, self.oled.history_index))

        # Draw the selection symbol -> TARVITSEEKO TÄTÄ??
        self.oled.text(self.oled.symbol, 5, self.oled.y + self.oled.line_height * self.oled.selected_index)

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
            self.run_history() # ei valmis
        
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
        self.oled.hrv_data_collected()
        time.sleep(2.5) # Show data collected text for 2.5 sec
        self.oled.fill(0)

        # Show the results and return main menu after press
        self.oled.show_hrv_results(hrv_results)
        self.oled.selected_index = 0 # update select mark to top of the oled
        self.return_main_menu_after_button_press()
    
    def run_kubios(self): # KESKEN
        self.oled.start_measurement_menu()  # show the start menu
        self.wait_for_button_press()

        self.oled.collecting_data()
        # kutsu tässä hrv-datan mittauksen funktiota

        # oled.hrv_data_collected() -> näytä kun mittaus valmis
        # lähetä tässä data kubiokseen?
    
    def run_history(self): # KESKEN
        
        # TODO: laita while True -loop, joka loppuu kun painaa nappia
        # history menua pitää näyttää aina uudelleen loopissa
            
        self.oled.history_menu(self.measurements)
            
        print(f'history index change menu -funktiosta: {self.oled.history_index}')
            
        # TODO: mark liikuttelu, kun rotarya pyöritetään !!!!
            
        value = self.get_fifo_value()
        self.detect_user_action(value)
        #self.oled.fill(0)
            
        #self.oled.text(self.oled.symbol, 5, self.oled.y + 12 * self.oled.history_index) # draw the selection symbol
        #self.oled.show()
            
            
        # wait for user to choose the measurement
        self.wait_for_button_press()
            
        # oled.py:ssä on show_selected_history -funktio (vaatii muokkausta vähän)
            
        if (self.oled.history_index is not None and
            0 <= self.oled.history_index < len(self.measurements)):
                
            # history measurements indexes can be 0 to 4 if list is full
            if self.oled.history_index < (len(self.measurements) - 1):
                    
                # show chosen measurement
                chosen_measurement = self.measurements[self.oled.history_index]
                self.oled.show_kubios_results(chosen_measurement)
                    
            else: # last index: return to main menu (if list is full: index = 5)
                self.oled.selected_menu = 'main_menu'
            
            
        # TODO: logiikka valinnalle (ks. main menun logiikka)
        # näytä kubios-mittauksen tulokset

        # tests, not working
        # value = get_fifo_value(rot)
        # detect_user_action(oled, value, measurements)
        # oled.text(oled.symbol, 5, oled.y + oled.line_height * oled.history_index)

    def wait_for_button_press(self):  # wait for user to press the button
        while True:
            if self.rot.fifo.has_data():
                value = self.get_fifo_value()
                if value == 0:
                    break

    def return_main_menu_after_button_press(self): # wait for button to be pressed, return menu
        while True:
            if self.rot.fifo.has_data():
                value = self.get_fifo_value()
                if value == 0:  # button press
                    self.oled.fill(0)
                    self.oled.selected_menu = 'main_menu'
                    self.oled.main_menu()  # return to main menu
                    break
