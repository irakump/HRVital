from fifo import Fifo
from piotimer import Piotimer
from machine import Pin, ADC


class isr_fifo(Fifo):
    def __init__(self, size, adc_pin_nr):
        super().__init__(size)
        self.av = ADC(adc_pin_nr) # sensor AD channel

    def handler(self, tid):
    # handler to read and store ADC value
    # this is to be registered as an ISR. Floats are not available in ISR
        self.put(self.av.read_u16())

pin_nr = 27
samples = isr_fifo(50, pin_nr) # create the improved fifo: size = 50,adc pin = pin_nr
tmr = Piotimer(mode = Piotimer.PERIODIC, freq = 250, callback = samples.handler)

while True:
    # to read:
    if not samples.empty():
        value = samples.get()
        print(value)