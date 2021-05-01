import setuptools

setuptools.setup(
    name='HardwareImplementation',
    version='0.1',
    package_dir={''},
    packages=setuptools.find_packages(where='src'),
    description='Hardware Implementation',
    install_requires=[
        'chess',
        'typing',
        'board',
        'busio',
        'digitalio',
        'adafruit_tca9548a',
        'adafruit_character_lcd.character_lcd_i2c',
        'adafruit_ht16k33',
        'adafruit_mcp230xx.mcp23017']
)