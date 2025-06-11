import board
import busio
import digitalio
import time
import sys
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_ds3502
import adafruit_tca9548a

''' NOTE: YOU might need to run the following commands:
    See: https://learn.adafruit.com/circuitpython-libraries-on-any-computer-with-mcp2221/windows
    # in CMD_PROMPT
        pip3 install hidapi
        pip install adafruit-circuitpython-ads1x15
        pip install adafruit-circuitpython-ds3502
        pip install adafruit-circuitpython-tca9548a
        pip3 install adafruit-blinka
        set BLINKA_MCP2221=1

    # in python to test board connection:
        import board
        dir(board)
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
V_REG_OFFSET = 0.25
V_REG_MULT = 2
ADS_GAIN = 2 / 3

ADS_CHAN_V_REG = ADS.P0
ADS_CHAN_I_REG = ADS.P1
ADS_CHAN_PEAK  = ADS.P2

'''
    DESCRIPTION:
        Converts the voltage sensed by the current sensor to a current value.
            See: https://www.ti.com/lit/ds/symlink/tmcs1108.pdf?ts=1749173283870&ref_url=https%253A%252F%252Fwww.ti.com%252Fproduct%252FTMCS1108%252Fpart-details%252FTMCS1108A1BQDR
    NOTE: Currently does not work, as current sensor is wired incorrectly on PCB.
'''
def curr_sens_conv(curr_volt):
    vs = 3.3
    s = 0.2
    return (curr_volt - (vs * 0.5) / s)

def test_adc(i2c):
    '''
    DESCRIPTION:
        Tests the ADC by reading in the channel voltages.
            See: https://learn.adafruit.com/adafruit-4-channel-adc-breakouts/python-circuitpython

    EXPECTED:
        ADC outputs should be the following, based on config in schematic:
            AIN0 : V_REG_IN 
            AIN1 : I_REG_IN
            AIN2 : PEAK_IN 
            AIN3 : Unused
    '''
    
    # ADS setup
    ads = ADS.ADS1115(i2c)
    ads.gain = ADS_GAIN
    # Channel read
    chan0 = AnalogIn(ads, ADS_CHAN_V_REG)
    chan1 = AnalogIn(ads, ADS_CHAN_I_REG)
    chan2 = AnalogIn(ads, ADS_CHAN_PEAK)
    chan3 = AnalogIn(ads, ADS.P3)
    print((
        "ADC readings:\n"
        f"\tA0 - V_REG_IN: {chan0.voltage * V_REG_MULT}\n"
        f"\tA1 - I_REG_IN: {curr_sens_conv(chan1.voltage)}\n"
        f"\tA2 - PEAK_IN:  {chan2.voltage}\n"
        f"\tA3 - UNUSED:    {chan3.voltage}\n"
    ))

'''
    DESCRPITION:
        Prints out all three channel values from the ADS.
'''
def adc_print(ads):
    # Channel read
    v_reg = AnalogIn(ads, ADS_CHAN_V_REG).voltage * V_REG_MULT
    i_reg = AnalogIn(ads, ADS_CHAN_I_REG).voltage
    peak = AnalogIn(ads, ADS_CHAN_PEAK).voltage 
    print((
        f"A0 - V_REG_IN: {v_reg}\n"
        f"A1 - I_REG_IN: {curr_sens_conv(i_reg)}\n"
        f"A2 - SIN_AMP_PEAK_IN:  {peak}\n"
    ))

'''
    DESCRIPTION:
        Helper function for test_gpio() to ensure input is binary.
'''
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
        GPIO Pin readings should match the user input, probe at the SN74LVC 
        switch input.
    
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

    print("Enter GPIO 0 - 3 binary digits (0 or 1). Press Ctrl+C to quit.")
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
        Tests the MCP2221 I2C readout to view the TCA9548A and ADS11115.
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
    # Now scan addresses on each channel.
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
    print("\n")

def test_pot_old(i2c):
    '''
    DESCRIPTION:
        Tests the digital pots by initializing and writing all pot values to 64
            See: https://docs.circuitpython.org/projects/ds3502/en/latest/

    EXPECTED:
        I2C should connect without failure, if there is a failure, please debug. 
        Pot resistances should be set to halfway (5k)
        Can disconnect pots from series resistors and probe resistance.
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
    
sq_tri_freq_map =  {
    'low': [1,1],
    'mid': [1,0],
    'high': [0,0]
}

def config_sq_tri(sw_pot, fdbk_pot, sq_tri_cap0, sq_tri_cap1, ads):
    '''
    Tests the square and triangle wave outputs.
    '''
    while True:
        try:
            user_input = input("Sq/Tri configurator: Enter RC pot (0–127), FDBK pot (0-127), Freq mode (low, mid, high) or 'exit': ").strip()
            if user_input.lower() == 'exit':
                print("Exiting.")
                break

            # Split and parse the input
            parts = user_input.split()
            if len(parts) != 3:
                print("Please enter values: rc_pot fdbk_pot freq_mode")
                continue

            sw_pot_val = int(parts[0])
            fdbk_pot_val = int(parts[1])
            freq_mode = parts[2]

            # Validate ranges
            if not (POT_MIN_BIT <= sw_pot_val <= POT_MAX_BIT):
                print("sw_pot value must be between 0 and 127.")
                continue
            
            if not (POT_MIN_BIT <= fdbk_pot_val <= POT_MAX_BIT):
                print("fdbk_pot value must be between 0 and 127.")
                continue

            if freq_mode not in sq_tri_freq_map:
                print("Freq mode must be: low, mid, or high.")
                continue
            sw_pot_val = int(parts[0])
            fdbk_pot_val = int(parts[1])
            
            cap0 = sq_tri_freq_map[freq_mode][0]
            cap1 = sq_tri_freq_map[freq_mode][1]

            # Set values
            sw_pot.wiper = sw_pot_val
            fdbk_pot.wiper = fdbk_pot_val
            sq_tri_cap0.value = cap0
            sq_tri_cap1.value = cap1
            # Print updated values and ADS readings.
            print(f"\tSW_POT: {sw_pot_val} \n\tFDBK_POT:{fdbk_pot_val} \n\tCAP1: {cap1} \n\tCAP0: {cap0}\n")
            adc_print(ads)
        # Handle faulty output
        except ValueError:
            print("Invalid input. Format: <RC_POT 0–127> <FBK_POT 0-127> <Freq mode (low/mid/high)")

sine_freq_map = {
    'low' : [0,0],
    'mid' : [1,1],
    'high': [0,1]
}

def config_sine(rc_pots, amp_pot, sine_cap0, sine_cap1,ads):
    while True:
        try:
            # Get main user input
            user_input = input("Sin configurator: Enter RC pot (0-127), Amp pot (0-127), and freq mode (low, mid, high) or 'exit': ").strip()

            if user_input.lower() == 'exit':
                print("Exiting.")
                break

            else:
                 # Split and parse the input
                parts = user_input.split()
                if len(parts) != 3:
                    print("Please enter exactly 3 values: RC_POT AMP_POT Freq mode")
                    continue
                rc_pot_val = int(parts[0])
                amp_pot_val = int(parts[1])
                if not (POT_MIN_BIT <= rc_pot_val <= POT_MAX_BIT):
                    print(f"Wiper value must be between {POT_MIN_BIT} and {POT_MAX_BIT}.")
                    continue
                
                freq_mode = parts[2]
                if freq_mode not in sq_tri_freq_map:
                    print("Freq mode must be: low, mid, or high.")
                    continue
                
                cap0 = sine_freq_map[freq_mode][0]
                cap1 = sine_freq_map[freq_mode][1]

                for rc_pot in rc_pots:
                    rc_pot.wiper = rc_pot_val
                amp_pot.wiper = amp_pot_val
                sine_cap0.value = cap0
                sine_cap1.value = cap1
                print(f"\tRC_POT: {rc_pot_val} \n\tAMP_POT: {amp_pot.wiper} \n\tCAP_1: {cap1} \n\tCAP_0: {cap0}\n")
                
                adc_print(ads)

        # Handle faulty output
        except ValueError:
            print("Invalid input. Format: <RC_POT 0–127> <AMP_POT 0-127> <Freq mode (low/mid/high)")
        
def run_all_tests(i2c):
    test_gpio()
    test_i2c(i2c)
    test_pot_old(i2c)
    test_adc(i2c)

def main():
    #I2C 
    i2c = board.I2C()

    # Comment this out to stop setup tests.
    # run_all_tests(i2c)

    # ADS setup
    ads = ADS.ADS1115(i2c)
    ads.gain = ADS_GAIN

    # Setup GPIO
    gpio0 = digitalio.DigitalInOut(board.G0)
    gpio1 = digitalio.DigitalInOut(board.G1)
    gpio2 = digitalio.DigitalInOut(board.G2)
    gpio3 = digitalio.DigitalInOut(board.G3)
    gpio0.direction = digitalio.Direction.OUTPUT
    gpio1.direction = digitalio.Direction.OUTPUT
    gpio2.direction = digitalio.Direction.OUTPUT
    gpio3.direction = digitalio.Direction.OUTPUT
    
    # Setup mux. These are the pots that currently work
    tca =               adafruit_tca9548a.TCA9548A(i2c)
    sq_tri_bus =        tca[CHAN_SQR_TRI]
    sin_bus =           tca[CHAN_SIN]
    pot_sq_tri_rc =     adafruit_ds3502.DS3502(sq_tri_bus, address=ADDR_SQ_TRI_RC)
    pot_sq_tri_fbk =    adafruit_ds3502.DS3502(sq_tri_bus, address=ADDR_SQ_TRI_FBK)
    pot_sin1 =          adafruit_ds3502.DS3502(sin_bus,    address=ADDR_SIN1)
    pot_sin2 =          adafruit_ds3502.DS3502(sin_bus,    address=ADDR_SIN2)
    pot_sin3 =          adafruit_ds3502.DS3502(sin_bus,    address=ADDR_SIN3)
    pot_amp  =          adafruit_ds3502.DS3502(sin_bus,    address=ADDR_AMP)

    while True:
        try:
            user_input = input("Enter the following:\n "
                               "\t'tests': tests initialization and connection of digital components"
                               "\n\t'sin': configures the sine wave"
                               "\n\t'sq_tri': configures the square and triangle wave"
                               "\n\t'exit': exits the program\n")
           
            if user_input.lower() == 'exit':
                print("Exiting.")
                sys.exit(0)
            
            elif user_input == 'sq_tri':
                config_sq_tri(pot_sq_tri_rc, pot_sq_tri_fbk, gpio2, gpio3, ads)
            elif user_input == 'sin':
                config_sine([pot_sin1, pot_sin2, pot_sin3], pot_amp, gpio0, gpio1, ads)
            elif user_input == 'tests':
                run_all_tests(i2c)
            else:
                raise ValueError
        # Handle faulty output
        except ValueError:
            print("Invalid input. Enter 'tests', 'sin', 'sq_tri', or 'exit'")

if __name__ == "__main__":
    main()
