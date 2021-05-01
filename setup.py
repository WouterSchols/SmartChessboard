import setuptools

setuptools.setup(
    name='SmartChessboard',
    version='1.0',
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where='src'),
    url='https://github.com/WouterSchols/SmartChessboard',
    license='',
    author='wouter',
    description='Framework for smart chessboard',
    install_requires=[
        'Adafruit-Blinka',
        'adafruit-circuitpython-74hc595',
        'adafruit-circuitpython-busdevice',
        'adafruit-circuitpython-charlcd',
        'adafruit-circuitpython-ht16k33',
        'adafruit-circuitpython-mcp230xx',
        'adafruit-circuitpython-tca9548a',
        'Adafruit-PlatformDetect',
        'Adafruit-PureIO',
        'adafruit-python-shell',
        'args',
        'chess',
        'pkg-resources',
        'pyftdi',
        'pyserial',
        'PySimpleGUI',
        'pyusb',
        'rpi-ws281x',
        'RPi.GPIO',
        'selenium',
        'setuptools',
        'sysv-ipc',
        'clint',
        'selenium',
        'urllib3'],
    tests_require=[
        'mock'
    ],
    test_suite="tests")

