import board
import busio
import adafruit_ds3502
import digitalio
import time
import sys
# pip install adafruit-circuitpython-ds3502

SINE_RES_ADDR = 0x28
SW_RES_ADDR = 0x29
FDBK_RES_ADDR = 0x2A

POT_MIN_BIT = 0
POT_MAX_BIT = 127

# Min and max sweep times, in MS
SWEEP_MIN_DELAY = 0
SWEEP_MAX_DELAY = 2000

'''
Conducts the sine test by adjusting the digital potentiometer.
There is an option to manually set the bit value or sweep through from 0 to 127 with a specified duration.
'''
def sine_test(pot):
    while True:
        try:
            # Get user input
            user_input = input("SINE TEST: Enter wiper value (0–127) or sweep or exit: ").strip()
            if user_input.lower() == 'exit':
                print("Exiting.")
                sys.exit(0)
            # In sweep mode, go from pot LOWEST bit to HIGHEST bit with a duration
            elif user_input.lower() == 'sweep':
                delay = int(input("Enter duration between each bit value (ms): ").strip())
                if SWEEP_MIN_DELAY <= delay <= SWEEP_MAX_DELAY:
                    for i in range(POT_MIN_BIT, POT_MAX_BIT):
                        pot.wiper = i
                        time.sleep(delay / 1000.0)
                else:
                    ("Must be number from 0-100")
            # Manual mode, enter the value to set the pot to
            value = int(user_input)
            if POT_MIN_BIT <= value <= POT_MAX_BIT:
                pot.wiper = value
                print(f"Wiper set to: {pot.wiper}")
            else:
                print(f"Value must be between {POT_MIN_BIT} and {POT_MAX_BIT}.")
        # Handle faulty input
        except ValueError:
            print(f"Invalid input. Please enter an integer from {POT_MIN_BIT} to {POT_MAX_BIT} or select the sweep function.")

'''
Conducts the test for square/triangle wave by allowing for input to adjust
both potentiometers. The user can also select the capacitor to use
from the capacitor bank with GPIO.
'''

def square_tri_test(sw_pot, fdbk_pot, gpio0, gpio1):

    while True:
        try:
            user_input = input("Enter wiper (0–127), bit0 (0/1), bit1 (0/1), or 'exit': ").strip()
            if user_input.lower() == 'exit':
                print("Exiting.")
                break

            # Manual mode

            # Split and parse the input
            parts = user_input.split()
            if len(parts) != 4:
                print("Please enter exactly four values: sw_pot fdbk_pot bit0 bit1")
                continue

            sw_pot_val = int(parts[0])
            fdbk_pot_val = int(parts[1])
            bit0 = int(parts[2])
            bit1 = int(parts[3])

            # Validate ranges
            if not (POT_MIN_BIT <= sw_pot_val <= POT_MAX_BIT):
                print("sw_pot value must be between 0 and 127.")
                continue
            
            if not (POT_MIN_BIT <= fdbk_pot_val <= POT_MAX_BIT):
                print("fdbk_pot value must be between 0 and 127.")
                continue

            if bit0 not in [0, 1] or bit1 not in [0, 1]:
                print("bit0 and bit1 must be either 0 or 1.")
                continue

            # Set values
            sw_pot.wiper = sw_pot_val
            fdbk_pot.wiper = fdbk_pot_val
            gpio0.value = bit0
            gpio1.value = bit1
            print(f"SW_POT set to {sw_pot_val}, FDBK_POT set to {fdbk_pot_val}, GPIO0 = {bit0}, GPIO1 = {bit1}")

        # Handle faulty output
        except ValueError:
            print("Invalid input. Format: <wiper 0–127> <bit0 0/1> <bit1 0/1> or choose sweep option.")
def main():
    # Setup I2C connection
    i2c = busio.I2C(board.SCL, board.SDA)
    # Setup potentiometer connection
    sine_pot = adafruit_ds3502.DS3502(i2c, address=SINE_RES_ADDR)
    sw_pot = adafruit_ds3502.DS3502(i2c, address=SW_RES_ADDR)
    fdbk_pot = adafruit_ds3502.DS3502(i2c, address=FDBK_RES_ADDR)
    # Setup GPIO
    gpio0 = digitalio.DigitalInOut(board.G0)
    gpio0.direction = digitalio.Direction.OUTPUT
    gpio1 = digitalio.DigitalInOut(board.G1)
    gpio1.direction = digitalio.Direction.OUTPUT

    #sine_test(sine_pot)
    square_tri_test(sw_pot, fdbk_pot, gpio0, gpio1)
if __name__ == "__main__":
    main()
###                rc_pot  fdbk_pot   gpio0  gpio1    cap used
### 116kHz           127    127       1      0          c39 220pF
### 19.6kHz           0     74        1      0          c39 220pF
### 96kHz           127    127        0      0          c38 3nf
### 15.9 kHz         0      74        0      0          c38 3nf
##  24.6 kHz        127     127       0      1           C37  22 nF
##  3.9kHz          0       74        0      1           c37  22 nF
##  1.15 kHz        127     127       1      1           c35  470 nf
### 160 Hz          0       74        1      1           C35  470 nF