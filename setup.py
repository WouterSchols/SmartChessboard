import setuptools

setuptools.setup(
    name='SmartChessboard',
    version='0.1',
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where="src"),
    url='https://github.com/WouterSchols/SmartChessboard',
    license='',
    author='wouter',
    author_email='',
    description='Framework for smart chessboard',
    install_requires=[
        'Adafruit-Blinka',
        'adafruit-circuitpython-busdevice',
        'adafruit-circuitpython-ht16k33',
        'adafruit-circuitpython-mcp230xx',
        'adafruit-circuitpython-tca9548a',
        'Adafruit-PlatformDetect',
        'Adafruit-PureIO',
        'adafruit-python-shell',
        'args',
        'chess',
        'clint',
        'mock',
        'numpy',
        'pyftdi',
        'pyserial',
        'pyusb',
        'selenium=',
        'urllib3'
    ]
)
