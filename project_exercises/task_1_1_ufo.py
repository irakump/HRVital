import time
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C

"""
Task 1.1
Implement a program that uses the two development board buttons to control a “UFO”. The UFO is
shown at the bottom of the screen with characters “<=>”. SW0 and SW2 are used to move the UFO left
and right. The program must stop the UFO at the edges of the screen so that it is completely visible.
When UFO is at left edge it must only be possible to move the UFO right and vice versa.
The font size is 8x8 pixels.
"""

button0 = Pin(9, Pin.IN, Pin.PULL_UP) # SW0
button2 = Pin(7, Pin.IN, Pin.PULL_UP) # SW2
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)

x = 51 # middle point 63 - 12 (width of the ufo is 24)
y = 55
colour = 1
ufo = '<=>' # ufo takes 3x8 = 24 pixels (width)

oled.fill(0) # clear display
oled.text(ufo, x, y, colour)
oled.show()

while True:
    oled.fill(0)
    if button0() == 0:
        oled.text(ufo, x, y, colour)
        if x % 4 == 0: # show on every 4 pixels
            oled.show()        
        x -= 1
        if x <= 0:
            x = 0

    elif button2() == 0:
        oled.text(ufo, x, y, colour)
        if x % 4 == 0: 
            oled.show()
        x += 1
        if x >= 103: # 127-24 = 103
            x = 103

