from src.Hardware.HardwareDisplay import Lcd
import board
import busio
import adafruit_tca9548a

i2c = busio.I2C(board.SCL, board.SDA)
tca = adafruit_tca9548a.TCA9548A(i2c, address=0x71)
display = Lcd(0x27, tca[6])
display.lcd_display_string("Hello world", 1)
