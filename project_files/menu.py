import time

# Menu helpers
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

        return None  # returns none, if fifo empty

    def detect_user_action(self, fifo_value):  # tarvitsee nyt parametrina listan kubios-mittauksista = measurements
        # read fifo value
        if fifo_value == 1:
            self.oled.selected_index += 1
        elif fifo_value == -1:
            self.oled.selected_index -= 1
        elif fifo_value == 0:  # rotary button pressed
            self.update_selected_menu()  # update the selected menu variable

            # TODO: kun painaa nappia kesken mittauksen tai tulosten jälkeen, palaa menuun

        # update history index
        if self.oled.selected_menu == 'history':
            if fifo_value == 1:
                self.oled.history_index += 1
            elif fifo_value == -1:
                self.oled.history_index -= 1

        # prevent overscrolling
        if self.oled.selected_menu == 'main_menu':
            self.oled.selected_index = min(3, max(0, self.oled.selected_index))
        elif self.oled.selected_menu == 'history':
            self.oled.history_index = min(len(self.measurements), max(0, self.oled.history_index))

        self.oled.text(self.oled.symbol, 5, self.oled.y + self.oled.line_height * self.oled.selected_index)  # draw the selection symbol

        # update display
        if self.oled.selected_menu == 'main_menu':
            self.oled.main_menu()

        return self.oled.selected_menu

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

    def change_menu(self):
        if self.oled.selected_menu == 'main_menu':
            self.oled.main_menu()

        elif self.oled.selected_menu == 'hr':
            self.oled.start_measurement_menu()
            self.hr.reset_button()
            measurement_on = self.hr.run2()

            if not measurement_on:  # measurement_on == False, user pressed to stop measurement
                self.oled.selected_menu = 'main_menu'

                self.rot.clear()  # clear the fifo
                self.hr.measuring = False

                self.oled.fill(0)
                self.oled.main_menu()
                time.sleep(0.1)

                return self.oled.selected_menu  # return to main loop

        elif self.oled.selected_menu == 'hrv':
            self.oled.start_measurement_menu()  # show the start menu
            self.wait_for_button_press()

            # HRV measurement after the press
            self.oled.fill(0)
            self.oled.collecting_data()  # update the oled
            self.oled.fill(0)
            
            hrv_results = self.hrv.get_basic_hrv_analysis()  # collect data and analyse
            self.oled.hrv_data_collected()
            time.sleep(2.5)
            self.oled.fill(0)

            self.oled.show_hrv_results(hrv_results)  # show results
            self.return_main_menu_after_button_press()  # return main menu
            return self.oled.selected_menu

        elif self.oled.selected_menu == 'kubios':
            self.oled.start_measurement_menu()  # show the start menu
            self.wait_for_button_press()

            self.oled.collecting_data()
            # kutsu tässä hrv-datan mittauksen funktiota

            # oled.hrv_data_collected() -> näytä kun mittaus valmis
            # lähetä tässä data kubiokseen?
            return self.oled.selected_menu

        elif self.oled.selected_menu == 'history':
            self.oled.history_menu(self.measurements)
            # TODO: logiikka valinnalle (ks. main menun logiikka)
            # rivien lkm riippuu measurements-listan koosta (max 4)
            # -> indeksien mukaan mittauksen valinta? indeksi 0 -> measurements[0]?
            # detect_user_action-funktiossa on history_index

            # tests, not working
            # value = get_fifo_value(rot)
            # detect_user_action(oled, value, measurements)
            # oled.text(oled.symbol, 5, oled.y + oled.line_height * oled.history_index)
            return self.oled.selected_menu

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
