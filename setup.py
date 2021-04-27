import setuptools

setuptools.setup(
    name='SmartChessboard',
    version='0.1',
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where='src'),
    url='https://github.com/WouterSchols/SmartChessboard',
    license='',
    author='wouter',
    author_email='',
    description='Framework for smart chessboard',
    install_requires=[
        'args',
        'chess',
        'clint',
        'numpy',
        'pyftdi',
        'pyserial',
        'pyusb',
        'selenium',
        'urllib3',
        'PySimpleGUI'],
    tests_require=[
        'mock'
    ],
    test_suite="tests",

)
