import time
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C


sw_0 = Pin(9, Pin.IN, Pin.PULL_UP) # swo_0 pin 9
sw_1 = Pin(8, Pin.IN, Pin.PULL_UP)
sw_2 = Pin(7, Pin.IN, Pin.PULL_UP)

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000) 

oled_width =128
oled_height =64
oled =SSD1306_I2C(oled_width, oled_height, i2c)

x = 0
y = 32 
colour = 1

while True:
    x+=1
    if x >= oled_width:
        x=0
       
    
    if sw_0() == 0: # move up
        y -= 1
        if y<0: 
           y=0    
            
        
    elif sw_2() == 0:   # move down
        y+=1
        if y >= oled_height:
             y = oled_height-1
        
   
    elif sw_1() == 0:   # clear screen
        oled.fill(0)
        x = 0   #reset
        y = 32  
        
       
    oled.pixel(x, y, colour)
    oled.show()        
    
 
    