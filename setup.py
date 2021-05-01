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
        'PySimpleGUI',
        'chess',
        'time',
        'typing',
        'datetime',
        'selenium',
        'threading',
        'copy',
        'adafruit-circuitpython-charlcd'
    ],
    tests_require=[
        'mock'
    ],
    test_suite="tests")
