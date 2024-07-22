import time
import math
import struct
import board
import busio
import pwmio
import digitalio
import analogio
import neopixel
import rotaryio
from adafruit_debouncer import Debouncer
# import usb_cdc
# import supervisor

from tmc import TMC_2209_reg as rg
from tmc.TMC_2209_cp_uart import *
from tmc.TMC_2209_stppr import *

from board_layout import pin_map as pm

# usb_serial = usb_cdc.data

num_pixel = 1

pixels = neopixel.NeoPixel(pm.LED_PIN, num_pixel, brightness=0.5, auto_write=False)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 128, 0)
MAGENTA = (255, 0, 255)
PINK = (192, 64, 64)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
WHITE = (128, 128, 128)
pixels.fill(PINK)
pixels.show()

LAMP = pwmio.PWMOut(pm.HB_PWM_PIN, frequency=1000)
lamp_is_off = True

stppre = TMC2209_stp_dir(pm.EN_DIR, pm.EN_STEP, pm.EN_EN, 'en', True)
stpprx = TMC2209_stp_dir(pm.Y_DIR, pm.Y_STEP, pm.Y_EN, 'yprt', False)
uart_x = TMC_2209_cp_uart(pm.TMC_TX4, pm.TMC_RX4, 115200, 1)
j = 0

steps = 100*200
speed = 1500

print("Hello")

encoder = rotaryio.IncrementalEncoder(pm.Y_STOP, pm.X_STOP)
button = digitalio.DigitalInOut(pm.TH0)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP
sw = Debouncer(button, interval=0.01)

lamp_pin = digitalio.DigitalInOut(pm.THB)
lamp_pin.direction = digitalio.Direction.INPUT
lamp_pin.pull = digitalio.Pull.UP
sw1 = Debouncer(lamp_pin, interval=0.1)

move_multiplier = 1
stepper_to_move = None
lamp_intensity = 0
default_intensity = 2048
pressed = None
last_position = 0
menu_level = 0
num_items = 8
menu_pos = 0

def stepper_en_disable(stppr_motor):
    if stppr_motor.isEnabled:
        stppr_motor.disable()
        print(stppr_motor.name, "is disabled")
        pixels.fill(RED)
    else:
        stppr_motor.enable()
        print(stppr_motor.name, "is enabled")
        pixels.fill(GREEN)

while True:
    sw.update()
    sw1.update()
    position = encoder.position
    if last_position is None or position != last_position:
        # print(last_position)
        to_move = position-last_position
        if menu_level == 0:
            menu_pos = math.fabs(math.fmod(position,num_items))
            print("Menu level:", menu_level, "Item:", menu_pos)
            if menu_pos <= 2:
                pixels.fill(ORANGE)
            elif menu_pos <= 5 and menu_pos > 2:
                pixels.fill(CYAN)
            elif menu_pos > 5:
                pixels.fill(WHITE)            
        if menu_level == 1:
            # print(position)
            if stepper_to_move == None:
                print("SELECT MOTOR FIRST")
                pixels.fill(MAGENTA)
            elif not stepper_to_move.isEnabled:
                print("Enable motors first!!")
                pixels.fill(BLUE)
            else:
                stepper_to_move.move_blocking(move_multiplier*to_move*200, speed)
        if menu_level == 2.5:
            if lamp_intensity <= 4096 and lamp_intensity >= 0:
                lamp_intensity += 100*to_move
            elif lamp_intensity > 4096:
                lamp_intensity -= math.floor(math.fabs(50*to_move))
            else:
                lamp_intensity += math.floor(math.fabs(to_move))
            print(lamp_intensity)
        if menu_level == 2:
            menu_level = 0
            # Leave out of menu if don't want to edit intensity
            
    if sw.fell:
        print("Pressed")
        if menu_level == 0:
            menu_level = 1
            print("menu_level: ", menu_level)
            
            if menu_pos <= 2:
                stepper_to_move = stppre
                move_multiplier = 1
                speed = 1800
                print("selected_stepper", stepper_to_move.name)
                stepper_en_disable(stepper_to_move)
            elif menu_pos <= 5 and menu_pos > 2:
                stepper_to_move = stpprx
                move_multiplier = 10
                speed = 5000
                print("selected_stepper", stepper_to_move.name)
                stepper_en_disable(stepper_to_move)
            elif menu_pos > 5 and not lamp_is_off:
                menu_level = 2.5
            print("menu_level: ", menu_level)

        elif menu_level == 1:
            print("menu_level: ", menu_level)
            stepper_en_disable(stepper_to_move)
            menu_level = 0
            print("menu_level_set_to: ", menu_level)

        elif menu_level == 2:   # Get into intensity edit mode
            menu_level = 2.5
            print("menu_level_set_to: ", menu_level)
        elif menu_level == 2.5: # Get out of intensity edit mode
            menu_level = 0
            print("menu_level_set_to: ", menu_level)
    
    if sw1.fell:
        # print("Its going low!!")
        if lamp_is_off:
            pixels.fill(WHITE)
            lamp_intensity = default_intensity
            menu_level = 2
            lamp_is_off = False
            print("Lamp on!")
        else:
            pixels.fill(RED)
            lamp_intensity = 0
            lamp_is_off = True
            menu_level = 0
            print("Lamp off!")
            
        # time.sleep(2)
    last_position = position
    LAMP.duty_cycle = lamp_intensity
    pixels.show()