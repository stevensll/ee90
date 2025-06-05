import board
import busio
import digitalio
import time
import sys
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_ds3502
import adafruit_tca9548a

from CAT5132 import CAT5132
''' NOTE: YOU might need to run the following commands:
    See: https://learn.adafruit.com/circuitpython-libraries-on-any-computer-with-mcp2221/windows
    # in CMD_PROMPT
        pip3 install hidapi
        pip3 install adafruit-blinka

        set BLINKA_MCP2221=1

    # in python
        import board
        dir(board)

    # in CMD_PROMPT
        pip install adafruit-circuitpython-ads1x15
        pip install adafruit-circuitpython-ds3502
        pip install adafruit-circuitpython-tca9548a

'''
# I2C Addresses for pots
ADDR_SQ_TRI_RC =    0x28
ADDR_SQ_TRI_FBK =   0x29
CHAN_SQR_TRI =      0

ADDR_SIN1 =         0x28
ADDR_SIN2 =         0x29
ADDR_SIN3 =         0x2A
ADDR_AMP =          0x2B
CHAN_SIN =          1

POT_MIN_BIT = 0
POT_MAX_BIT = 127

def test_adc():
    '''
    DESCRIPTION:
        Tests the ADC by reading in the channel voltages.
            See: https://learn.adafruit.com/adafruit-4-channel-adc-breakouts/python-circuitpython

    EXPECTED:
        ADC outputs should be the following, based on config in schematic:
            AIN0 : V_REG_IN 
            AIN1 : I_REG_IN
            AIN2 : PEAK_IN 
    '''
    # I2C setup
    i2c = board.I2C()
    # ADS setup
    ads = ADS.ADS1015(i2c)
    # Channel read
    chan0 = AnalogIn(ads, ADS.P0)
    chan1 = AnalogIn(ads, ADS.P1)
    chan2 = AnalogIn(ads, ADS.P2)
    chan3 = AnalogIn(ads, ADS.P3)
    print((
        f"A0 - V_REG_IN: {chan0.voltage}\n"
        f"A1 - I_REG_IN: {chan1.voltage}\n"
        f"A2 - PEAK_IN:  {chan2.voltage}\n"
        f"A3 - UNUSED:    {chan3.voltage}\n"
    ))


def is_valid_binary_input(user_input):
    return len(user_input) == 4 and all(char in ('0', '1') for char in user_input)

def test_gpio():
    '''
    DESCRIPTION:
        Tests MCP2221 GPIO Pins by initializing and writing all pins HIGH
            See pin layout: https://learn.adafruit.com/circuitpython-libraries-on-any-computer-with-mcp2221/overview
            NOTE: ON PCB, our pin layout wrong -> must FLIP MCP UPSIDE DOWN
        
        Pin mappings, based on schematic:
            GPIO 0 : SIN_BIT0
            GPIO 1 : SIN_BIT1
            GPIO 2 : SQ_TRI_BIT0
            GPIO 3 : SQ_TRI_BIT1

    EXPECTED:
        ALL GPIO Pins should be HIGH (3.3V)
        Probe SQ_TRI_BIT0 at R12
        Probe SQ_TRI_BIT1 at R9
        
        SINBIT0 should modify SIN_CAP1_0, SIN_CAP2_0, SIN_CAP3_0
        SINBIT1 should modify SIN_CAP1_1, SIN_CAP2_1, SIN_CAP3_1
    '''
    # Setup GPIO
    gpio0 = digitalio.DigitalInOut(board.G0)
    gpio1 = digitalio.DigitalInOut(board.G1)
    gpio2 = digitalio.DigitalInOut(board.G2)
    gpio3 = digitalio.DigitalInOut(board.G3)
    gpio0.direction = digitalio.Direction.OUTPUT
    gpio1.direction = digitalio.Direction.OUTPUT
    gpio2.direction = digitalio.Direction.OUTPUT
    gpio3.direction = digitalio.Direction.OUTPUT

    print("Enter 4 binary digits (0 or 1). Press Ctrl+C to quit.")
    while True:
        user_input = input("Input:").strip()
        if is_valid_binary_input(user_input):
            vals = [int(bit) for bit in user_input]
            # Write to the GPIO.
            gpio0.value = vals[0]
            gpio1.value = vals[1]
            gpio2.value = vals[2]
            gpio3.value = vals[3]
            print ((
                "Set the following:\n"
                f"\tSQ_TRI_BIT0, U141 pin 6 :  {gpio2.value}\n"
                f"\tSQ_TRI_BIT1, U143 pin 6  : {gpio3.value}\n\n"
                f"\tSIN_CAP1_0,  U142 pin 6  : {gpio0.value}\n"
                f"\tSIN_CAP2_0,  U10  pin 6  : {gpio0.value}\n"
                f"\tSIN_CAP3_0,  U12  pin 6  : {gpio0.value}\n\n"
                f"\tSIN_CAP1_1,  U140 pin 6  : {gpio1.value}\n"
                f"\tSIN_CAP2_1,  U30  pin 6  : {gpio1.value}\n"
                f"\tSIN_CAP3_1,  U11  pin 6  : {gpio1.value}\n"
            ))
        else:
            print("Invalid input. Please enter exactly 4 binary digits (0 or 1).")

'''
    DESCRIPTION:
        Tests the MCP2221 I2C readout to view th eTCA9548A and ADS11115.
        Then tests the I2C addresses by connecting to the TCA9548A multiplexer and 
        reading the addresses on each channel.
            See: https://learn.adafruit.com/adafruit-tca9548a-1-to-8-i2c-multiplexer-breakout/circuitpython-python

    EXPECTED:
        For the MCP2221, the found addresses should be 0x48 (ADS) and 0x70 (TCA)
        For the TCA,
            Channel 0: 0x28, 0x29
            Channel 1: 0x28, 0x29, 0x2A, 0x2B
'''
def test_i2c(i2c):
    # Scan i2c addresses on the MCP2221 
    # Should find 0x48 (ADS), 0x70 (TCA)
    if i2c.try_lock():
        print("MCP2221 found addresses:", [hex(addr) for addr in i2c.scan()])
        i2c.unlock()
    
    tca = adafruit_tca9548a.TCA9548A(i2c)
    
    if tca[CHAN_SQR_TRI].try_lock():
        print(f"\tMux channel {CHAN_SQR_TRI} found:", end="")
        addresses = tca[CHAN_SQR_TRI].scan()
        print([hex(address) for address in addresses if address != 0x70 and address !=0x48])
        tca[CHAN_SQR_TRI].unlock()

    if tca[CHAN_SIN].try_lock():
        print(f"\tMux channel {CHAN_SIN} found:", end="")
        addresses = tca[CHAN_SIN].scan()
        print([hex(address) for address in addresses if address != 0x70 and address !=0x48])
        tca[CHAN_SIN].unlock()


def test_pot_old(i2c):
    '''
    DESCRIPTION:
        Tests the digital pots by initializing and writing all pot values to 64
            See: https://docs.circuitpython.org/projects/ds3502/en/latest/

    EXPECTED:
        I2C should connect without failure, if there is a failure, please debug. 
        Pot resistances should be set to halfway (5k)
        Can't really probe this, must test on the circuit itself if connected to power.
        Should check input to pots if the addresses are correct.
    '''
    # Mux setup
    tca = adafruit_tca9548a.TCA9548A(i2c)
    # Get the buses
    sq_tri_bus = tca[CHAN_SQR_TRI]
    sin_bus = tca[CHAN_SIN]
    # Setup potentiometer connection
    pot_sq_tri_rc =     adafruit_ds3502.DS3502(sq_tri_bus, address=ADDR_SQ_TRI_RC)
    pot_sq_tr_fbk =     adafruit_ds3502.DS3502(sq_tri_bus, address=ADDR_SQ_TRI_FBK)
    pot_sin1 =          adafruit_ds3502.DS3502(sin_bus, address=ADDR_SIN1)
    pot_sin2 =          adafruit_ds3502.DS3502(sin_bus, address=ADDR_SIN2)
    pot_sin3 =          adafruit_ds3502.DS3502(sin_bus, address=ADDR_SIN3)
    pot_amp  =          adafruit_ds3502.DS3502(sin_bus, address=ADDR_AMP)
    # Set the potentiometer value
    pot_sq_tri_rc.wiper = 64
    pot_sq_tr_fbk.wiper = 64
    pot_sin1.wiper =      64
    pot_sin2.wiper =      64
    pot_sin3.wiper =      64
    pot_amp.wiper  =      64
    

def square_tri_test(sw_pot, fdbk_pot, sq_tri_cap0, sq_tri_cap1):
    '''
    Tests the square and triangle wave outputs.
    '''
    while True:
        try:
            user_input = input("Enter RC pot (0–127), FDBK pot (0-127), Cap bit0 (0/1), Cap bit1 (0/1), or 'exit': ").strip()
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
            sq_tri_cap0.value = bit0
            sq_tri_cap1.value = bit1
            print(f"SW_POT set to {sw_pot_val}, FDBK_POT set to {fdbk_pot_val}, GPIO0 = {bit0}, GPIO1 = {bit1}")

        # Handle faulty output
        except ValueError:
            print("Invalid input. Format: <wiper 0–127> <bit0 0/1> <bit1 0/1> or choose sweep option.")

def main():
    i2c = board.I2C()
    
    test_adc()
    # test_gpio()
    test_i2c(i2c)
    # test_pot_old(i2c) # don't use yet, not all pots soldered.

    # Setup GPIO
    gpio0 = digitalio.DigitalInOut(board.G0)
    gpio1 = digitalio.DigitalInOut(board.G1)
    gpio2 = digitalio.DigitalInOut(board.G2)
    gpio3 = digitalio.DigitalInOut(board.G3)
    gpio0.direction = digitalio.Direction.OUTPUT
    gpio1.direction = digitalio.Direction.OUTPUT
    gpio2.direction = digitalio.Direction.OUTPUT
    gpio3.direction = digitalio.Direction.OUTPUT
    
    # Setup mux. These are the pots that currently work (6/5/2025 6:00 AM)
    tca = adafruit_tca9548a.TCA9548A(i2c)
    sq_tri_bus = tca[CHAN_SQR_TRI]
    pot_sq_tri_rc =  adafruit_ds3502.DS3502(sq_tri_bus, address=ADDR_SQ_TRI_RC)
    pot_sq_tri_fbk = adafruit_ds3502.DS3502(sq_tri_bus, address=ADDR_SQ_TRI_FBK)
    
    square_tri_test(pot_sq_tri_rc, pot_sq_tri_fbk, gpio2, gpio3)

if __name__ == "__main__":
    main()
