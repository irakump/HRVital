# input()

import random
import time
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_width = 128
oled_height = 64
oled = SSD1306_I2C(oled_width, oled_height, i2c)

inputs = []

while True:
    oled.fill(0)
    
    y = 0
    max_items = 6
    
    inputs.append(input())
    
    if len(inputs) > max_items:
        inputs.pop(0)
        
    for item in inputs:
        oled.text(str(item), 0, y, 1)
        y += 10
    oled.show()

