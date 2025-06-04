import board
import busio
import digitalio
import time
import sys
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_ds3502

''' NOTE: YOU might need to run the following commands:
    # in CMD_PROMPT
        set BLINKA_MCP2221=1

    # in python
        import board
        dir(board)

    # in CMD_PROMPT
        pip install adafruit-circuitpython-ads1x15
        pip install adafruit-circuitpython-ds3502
'''
# I2C Addresses for pots
ADDR_SQ_TRI_RC =    0x28
ADDR_SQ_TRI_FBK =   0x29

ADDR_SIN1 =         0x28
ADDR_SIN2 =         0x29
ADDR_SIN3 =         0x2A

ADDR_AMP =          0x2B

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
    # Write to the GPIO.
    gpio0.value = 1
    gpio1.value = 1
    gpio2.value = 1
    gpio3.value = 1


def test_pot():
    '''
    DESCRIPTION:
        Tests the digital pots by initializing and writing all pot values to 64
            See: https://docs.circuitpython.org/projects/ds3502/en/latest/

    EXPECTED:
        Pot resistances should be set to halfway (5k)
        Can't really probe this, must test on the circuit itself.
        
        Should check input to pots if the addresses are correct.
    '''
    # I2C setup
    i2c = board.I2C()
    # Setup potentiometer connection
    pot_sq_tri_rc =     adafruit_ds3502.DS3502(i2c, address=ADDR_SQ_TRI_RC)
    pot_sq_tr_fbk =     adafruit_ds3502.DS3502(i2c, address=ADDR_SQ_TRI_FBK)
    pot_sin1 =          adafruit_ds3502.DS3502(i2c, address=ADDR_SIN1)
    pot_sin2 =          adafruit_ds3502.DS3502(i2c, address=ADDR_SIN2)
    pot_sin3 =          adafruit_ds3502.DS3502(i2c, address=ADDR_SIN3)
    pot_amp  =          adafruit_ds3502.DS3502(i2c, address=ADDR_AMP)

    # Set the potentiometer value
    pot_sq_tri_rc.wiper = 64
    pot_sq_tr_fbk.wiper = 64
    pot_sin1.wiper =      64
    pot_sin2.wiper =      64
    pot_sin3.wiper =      64
    pot_amp.wiper  =      64

def main():
   test_adc()
   test_gpio()
   test_pot()

if __name__ == "__main__":
    main()
