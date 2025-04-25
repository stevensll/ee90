# thermal_control_template.py
#
# Template for thermal control program, Lab2 EE90
#
# Remember to run 
# set BLINKA_MCP2221=1
# test in python
#   import board
#   dir(board)
#
# DAC0 = Control setpoint
# DAC1 = Splitter excitation
# DAC2 = Ground reference
# DAC3 = Test
# AIN0 = Splitter  excitation
# AIN1 = Thermistor tap reading
# AIN2 = Ground reference
# AIN3 = Test

import board
import adafruit_mcp4728
import numpy as np
import time
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from datetime import datetime


# Thermistor constants, 
# see: https://www.eaton.com/content/dam/eaton/products/electronic-components/resources/data-sheet/eaton-nt-surface-mount-ntc-thermistor-data-sheet-elx1110-en.pdf
RB = 10000.0  # resistor in series with thermistor, Ohms
RT0 = 10000.0  # thermistor resistance at 25C, Ohms
T0_C = 25.0  # thermistor reference temperature, degrees C
BR = 3600.0  # B25/B50 ratio, unitless

SETPOINT = 300          # Temp in Kelvin 
KP = -1.1               # P Gain
KI = -0.035             # I Gain
KD = 0.0                # D Gain
PREVIOUS_ERROR = 0  
INTEGRAL = 0        
DT = 1                  # Time step, seconds  
RUN_TIME = 30           # PID run time, adjust as necessary,  minutes
INTEGRAL_BOUND = 250.0  # Max integral bound
DEADBAND = 0.075        # PID error is 0 if within this deadband range

# DAC Parameters
DAC_BITS = 16  # all adafruit circuit python is 16 bit, even though MCP4728 is 12 bit, bits
DAC_LIMIT = 3.3  # maximum output voltage from DAC, Volts (measured to be 3.287)

# functions
'''
Bounds a value to the specified bound, positive or negative.
'''
def clamp(val, bound):
    if abs(val) >= bound and val != 0:
        if val < 0:
            return -bound
        else:
            return bound
    else:
        return val

def calc_temperature(rb, rt0, t0_c, br, vcc, vt):
    '''
    calculate the thermistor temperature in Kelvin
    INPUTS
    rb: is the resistor in series with the thermistor
    rt0: is the thermistor reference resistance
    t0_c: is the thermistor reference temperature in C
    br: is the thermistor beta term
    vcc: is the splitter excitation voltage in V
    vt: is the sampled thermistor voltage in V
    RETURNS
    t_therm: the temperature of the thermistor in Kelvin
    '''
    rt = rb * vt / (vcc - vt)
    t0_k = t0_c + 273.15
    t_therm = 1.0 / ((1.0 / t0_k) + (1.0 / br) * np.log(rt / rt0))
    return t_therm


def pid_controller(setpoint, pv, kp, ki, kd, previous_error, integral, dt):
    '''
    pid_controller function
    INPUTS
    setpoint: is the process setpoint, same units as pv
    pv: is current process output, same units as setpoint
    kp: is the porportional term
    ki: is the integral term
    kd: is the derivative term
    previous_error: is setpoint-pv from the previous readings
    integral: accumualted error 
    dt: is the time step in sectonds
    RETURNS
    control: the control to be applied
    error: the difference between the setpoint and the incoming process reading
    integral: the updated integral error
    '''
    error = setpoint - pv
    if abs(error) < DEADBAND:
        error = 0.0
    integral += error * dt
    derivative = (error - previous_error) / dt
    control = kp * error + ki * integral + kd * derivative
    # Clamp the integral
    integral = clamp(integral, INTEGRAL_BOUND)
    return control, error, integral


def cond_dac_control(set_point, dac_limit, dac_bits):
    '''
    calculate dac output based on process setpoint
    INPUTS
    set_point: the output of the PID function
    dac_limit: the maximum voltage of the DAC, in volts
    dac_bits: the DAC resolution, in bits
    RETURNS
    set_dac: the DAC set point, in bits
    '''
    dac_max = (2**dac_bits) - 1  # Calculate max DAC value based on bit depth
    set_ideal = int(set_point * (dac_max / dac_limit))  # Scale setpoint to DAC range, output bits
    
    if set_ideal > dac_max:  #PID ask is greater than DAC MSB, set to DAC MSB
        set_dac = dac_max
    elif set_ideal < 0: #PID ask is less than DAC LSB, set to LSB
        set_dac = 0
    else: #PID ask is within DAC code space
        set_dac = set_ideal
        
    return set_dac

'''
    See: 
    https://learn.adafruit.com/adafruit-4-channel-adc-breakouts/python-circuitpython
    Report voltages on ADC pins.
        C0 - ADC0
        C1 - ADC1
        C2 - ADC2
        C3 - ADC3
'''
def test_adc():
    i2c = board.I2C()
    ads = ADS.ADS1015(i2c)
    chan0 = AnalogIn(ads, ADS.P0)
    chan1 = AnalogIn(ads, ADS.P1)
    chan2 = AnalogIn(ads, ADS.P2)
    chan3 = AnalogIn(ads, ADS.P3)
    print(f"C0 : {chan0.voltage}\nC1 : {chan1.voltage}\nC2 : {chan2.voltage}\nC3 : {chan3.voltage}")

''' See:
    https://learn.adafruit.com/adafruit-mcp4728-i2c-quad-dac/python-circuitpython
    Set voltages on DAC output pins. Check with a multimeter on board:
        3.3V   on VA - TP8 (DAC0)
        1.65V  on VB - TP7 (DAC1)
        0.825V on VC - TP6 (DAC2)
        0V     on VD - TP5 (DAC3)
'''
def test_dac():
    # open-up communications with USB, ADC, and DAC
    i2c = board.I2C()  # uses board.SCL and board.SDA
    mcp4728 = adafruit_mcp4728.MCP4728(i2c, adafruit_mcp4728.MCP4728_DEFAULT_ADDRESS)
    mcp4728.channel_a.value = 65500            
    mcp4728.channel_b.value = int(65535)
    mcp4728.channel_c.value = int(65535/4)
    mcp4728.channel_d.value = 0

def test_on_off():
    # H/W Setup
    i2c = board.I2C()  # uses board.SCL and board.SDA
    ads = ADS.ADS1015(i2c)
    chan0 = AnalogIn(ads, ADS.P0)
    chan1 = AnalogIn(ads, ADS.P1)
    mcp4728 = adafruit_mcp4728.MCP4728(i2c, adafruit_mcp4728.MCP4728_DEFAULT_ADDRESS)
    mcp4728.channel_b.value = int(65535)
    mcp4728.channel_c.value = 0
    mcp4728.channel_d.value = 0
    # Time
    now_date = datetime.now()
    current_time = now_date.strftime("_%Y_%m_%d_%H_%M_%S")
    start_time = time.time()
    # Data collection
    on_off_data = open('on_off_data' + current_time + '.csv', 'w')
    on_off_data.write('Time,Temperature\n')
    num_steps = int(RUN_TIME * 60 / DT)
    # Loop for 20 minutes - 10 on, 10 off
    for step in range(num_steps * 2):
        time_now = time.time() - start_time
        vcc = chan0.voltage
        vt = chan1.voltage
        current_temp = calc_temperature(RB, RT0, T0_C, BR, vcc, vt)
        print(f"Temperature is {current_temp:.3f}")
        # On for first 10 minutes, then off for next 10
        if (step <= num_steps):
            # NOTE: BJT is ON when DAC Output is OFF (0V)
            mcp4728.channel_a.value = 0 
        else:
            # NOTE: BJT is OFF when DAC Output is ON (3V)
            mcp4728.channel_a.value = 65535 

        on_off_data.write(f'{time_now},{current_temp}\n')
        time.sleep(DT)

    on_off_data.close()

def pid_test():
    # Setup hardware
    i2c = board.I2C()  # uses board.SCL and board.SDA
    ads = ADS.ADS1015(i2c)
    chan0 = AnalogIn(ads, ADS.P0)
    chan1 = AnalogIn(ads, ADS.P1)
    mcp4728 = adafruit_mcp4728.MCP4728(i2c, adafruit_mcp4728.MCP4728_DEFAULT_ADDRESS)
    # Make sure to set channel B (DAC1 on Alium ) to VCC 
    mcp4728.channel_b.value = int(2 ** DAC_BITS - 1)
    mcp4728.channel_c.value = 0
    mcp4728.channel_d.value = 0
    
    # Set up PID parameters
    PREVIOUS_ERROR = 0.0
    INTEGRAL = 0.0
    
    # Timing parameters
    now_date = datetime.now()
    current_time = now_date.strftime("_%Y_%m_%d_%H_%M_%S")
    plot_start_time = time.time()
    now_time = time.time()
    last_time = time.time()
    
    # Create file to analyze performance of loop
    data_file_pid = open('temp_data_pid' + current_time + '.csv', 'w')
    data_file_pid.write('Time,Temperature,DAC,Error,Integral\n')
    
    # Determine run time
    num_steps = int(RUN_TIME * 60 / DT)

    for step in range(num_steps):
        # Update time parameters
        now_time = time.time()
        plot_time_now = now_time - plot_start_time
        dt = now_time - last_time
        last_time = now_time

        # Calculate the temperature
        vcc = chan0.voltage
        vt = chan1.voltage
        current_temp = calc_temperature(RB, RT0, T0_C, BR, vcc, vt)
        
        # Get controller output 
        control_output, PREVIOUS_ERROR, INTEGRAL = pid_controller(
            SETPOINT, current_temp, KP, KI, KD, PREVIOUS_ERROR, INTEGRAL, dt
        )
        dac_value = cond_dac_control(control_output, DAC_LIMIT, DAC_BITS)
        
        # And set DAC
        mcp4728.channel_a.value = dac_value
        
        # Write to file
        data_file_pid.write(f'{plot_time_now},{current_temp},{dac_value},{PREVIOUS_ERROR},{INTEGRAL}\n')
        time.sleep(DT)
        
        # Debug print
        print(f"vt value {chan1.value}, vcc value {chan0.value}")
        print(f"Temperature is {current_temp:.3f} K against {SETPOINT} K setpoint")
        print(f"Dt is {dt}")
        print(f"Error is {PREVIOUS_ERROR:.3f} kP * Error is {KP * PREVIOUS_ERROR:.3f} Integral is {INTEGRAL:.3f}, KI *INT is {KI * INTEGRAL:.3f}")
        print(f"DAC setting is {dac_value * DAC_LIMIT / ((2**DAC_BITS)-1):.3f} V")

    data_file_pid.close()

# 2 hour test
# Change setpoint
# Start with 75% of maximum temperature (tmp - 300) * .75 + 300
# At 1 hour, 25% of maximum temperature (tmp - 300) * .25 + 300
LONG_RUN_TIME = 120 # in mins
MAX_TEMP = 313.547
MAX_75_VALUE = (MAX_TEMP - SETPOINT )* .75 + SETPOINT
MAX_25_VALUE = (MAX_TEMP - SETPOINT )* .25 + SETPOINT

def long_test():
    # Setup hardware
    i2c = board.I2C()  # uses board.SCL and board.SDA
    ads = ADS.ADS1015(i2c)
    chan0 = AnalogIn(ads, ADS.P0)
    chan1 = AnalogIn(ads, ADS.P1)
    mcp4728 = adafruit_mcp4728.MCP4728(i2c, adafruit_mcp4728.MCP4728_DEFAULT_ADDRESS)
    # Make sure to set channel B (DAC1 on Alium ) to VCC 
    mcp4728.channel_b.value = int(2 ** DAC_BITS - 1)
    mcp4728.channel_c.value = 0
    mcp4728.channel_d.value = 0
    
    # Set up PID parameters
    PREVIOUS_ERROR = 0.0
    INTEGRAL = 0.0
    
    # Timing parameters
    now_date = datetime.now()
    current_time = now_date.strftime("_%Y_%m_%d_%H_%M_%S")
    plot_start_time = time.time()
    now_time = time.time()
    last_time = time.time()
    
    # Create file to analyze performance of loop
    data_file_pid = open('temp_data_pid' + current_time + '.csv', 'w')
    data_file_pid.write('Time,Temperature,DAC,Error,Integral\n')
    
    # Determine run time
    num_steps = int(LONG_RUN_TIME * 60 / DT)

    for step in range(num_steps):
        # Update time parameters
        now_time = time.time()
        plot_time_now = now_time - plot_start_time
        dt = now_time - last_time
        last_time = now_time

        # Calculate the temperature
        vcc = chan0.voltage
        vt = chan1.voltage
        current_temp = calc_temperature(RB, RT0, T0_C, BR, vcc, vt)
        
        setpoint = 0
        # first half we want setopint to be 75 % max
        if (step <= num_steps / 2) :
            setpoint = MAX_75_VALUE
        else:
            setpoint = MAX_25_VALUE
        # Get controller output 
        control_output, PREVIOUS_ERROR, INTEGRAL = pid_controller(
            setpoint, current_temp, KP, KI, KD, PREVIOUS_ERROR, INTEGRAL, dt
        )
        dac_value = cond_dac_control(control_output, DAC_LIMIT, DAC_BITS)
        
        # And set DAC
        mcp4728.channel_a.value = dac_value
        
        # Write to file
        data_file_pid.write(f'{plot_time_now},{current_temp},{dac_value},{PREVIOUS_ERROR},{INTEGRAL}\n')
        time.sleep(DT)
        
        # Debug print
        # print(f"vt value {chan1.value}, vcc value {chan0.value}")
        print(f"Temperature is {current_temp:.3f} K against {setpoint} K setpoint")
        print(f"Dt is {dt}")
        print(f"Error is {PREVIOUS_ERROR:.3f} kP * Error is {KP * PREVIOUS_ERROR:.3f} Integral is {INTEGRAL:.3f}, KI *INT is {KI * INTEGRAL:.3f}")
        print(f"DAC setting is {dac_value * DAC_LIMIT / ((2**DAC_BITS)-1):.3f} V")

    data_file_pid.close()
def main():
    # test_dac()
    # test_adc()
    # test_on_off()
    pid_test()
    # long_test()

if __name__ == "__main__":
    main()