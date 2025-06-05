#I2C driver for CAT5132 digipot 
from time import sleep
from micropython import const
from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register.i2c_struct import UnaryStruct

__version__ = "0.0.1"

# Default I2C Address (A0=0, A1=0 for CAT5132)
_CAT5132_DEFAULT_ADDRESS = const(0x28) # 0101000

# Register Addresses and Commands from CAT5132 Datasheet
_AR_REGISTER_ADDRESS = const(0x02)      # Access Register address
_WCR_DR_DATA_ADDRESS = const(0x00)    # Data address for WCR after selection by AR
_DCR_DR_DATA_ADDRESS = const(0x00)    # Data address for DCR after selection by AR
_SELECT_WCR_COMMAND = const(0x80)     # Value to write to AR to select Wiper Control Register
_SELECT_DCR_COMMAND = const(0x00)     # Value to write to AR to select Default Control Register

class CAT5132:
    """
    Driver for the CAT5132 I2C Digital Potentiometer. EE 90-2025  
    https://www.onsemi.com/pdf/datasheet/cat5132-d.pdf  
    """

    _access_register_selector = UnaryStruct(_AR_REGISTER_ADDRESS, "B")
    _wiper_register_data = UnaryStruct(_WCR_DR_DATA_ADDRESS, "B")
    _default_register_data = UnaryStruct(_DCR_DR_DATA_ADDRESS, "B")


    def __init__(self, i2c_bus, address=_CAT5132_DEFAULT_ADDRESS):
        """
        Initializes the CAT5132 digital potentiometer.
        :param i2c_bus: The I2C bus to use (e.g., board.I2C() in CircuitPython).
        :param int address: The I2C address of the CAT5132 device (default is 0x28).
        """
        self.i2c_device = I2CDevice(i2c_bus, address)

    @property
    def wiper(self):
        """
        The current position of the potentiometer's wiper (0-127).
        The value read is 7-bit (0-127). The MSB read from the device is ignored (datasheet: comes back as '0').
        """

        self._access_register_selector = _SELECT_WCR_COMMAND #select WCR
        raw_value = self._wiper_register_data #read data from it
        return raw_value & 0x7F  # Ensure value is 7-bit, as MSB is ignored/0

    @wiper.setter
    def wiper(self, value):
        """
        Sets the position of the potentiometer's wiper.

        :param int value: The desired wiper position (0-127).

        """
        if not 0 <= value <= 127:
            raise ValueError("Wiper position value must be between 0 and 127.")

        self._access_register_selector = _SELECT_WCR_COMMAND
        self._wiper_register_data = value 
        return

    def set_default(self, value):
        """
        Sets the default position of the potentiometer's wiper.

        :param int value: The desired wiper position (0-127).

        """
        if not 0 <= value <= 127:
            raise ValueError("Default value must be between 0 and 127.")
        self._access_register_selector = _SELECT_DCR_COMMAND
        self._default_register_data = value
        #now verify a valid value was written by reading back the register 
        self._access_register_selector = _SELECT_DCR_COMMAND
        read_value = self._default_register_data
        if read_value != value:
            raise RuntimeError(f"Failed to set default value. Expected {value}, got {read_value}.")
        
        return
    
    @property
    def default_wiper(self):
        """
        The current default position of the potentiometer's wiper (0-127).
        The value read is 7-bit (0-127). The MSB read from the device is ignored (datasheet: comes back as '0').
        """
        self._access_register_selector = _SELECT_DCR_COMMAND
        raw_value = self._default_register_data
        return raw_value & 0x7F  # Ensure value is 7-bit, as MSB is ignored/0