import board
import busio
import adafruit_ds3502

# pip install adafruit-circuitpython-ds3502

SINE_RES_ADDR = 0x28
SW_RES_ADDR = 0x29
FDBK_ADDR = 0x2A

def pot_test():
    # Initialize I2C bus using MCP2221
    i2c = busio.I2C(board.SCL, board.SDA)

    # Create DS3502 instance at default I2C address 0x28
    pot = adafruit_ds3502.DS3502(i2c, address=SINE_RES_ADDR)

    # Set the wiper to midpoint (64 out of 127)
    pot.wiper = 64

    # Confirm the setting
    print("DS3502 wiper set to:", pot.wiper)

def set_test():
    # Initialize I2C bus via MCP2221
    i2c = busio.I2C(board.SCL, board.SDA)

    # DS3502 at I2C address 0x28 (change if needed)
    pot = adafruit_ds3502.DS3502(i2c, address=SINE_RES_ADDR)

    while True:
        try:
            user_input = input("Enter wiper value (0–127) or 'exit': ").strip()
            if user_input.lower() == 'exit':
                print("Exiting.")
                break

            value = int(user_input)
            if 0 <= value <= 127:
                pot.wiper = value
                print(f"Wiper set to: {pot.wiper}")
            else:
                print("Value must be between 0 and 127.")
        except ValueError:
            print("Invalid input. Please enter an integer from 0 to 127.")

def main():
    pot_test()

if __name__ == "__main__":
    main