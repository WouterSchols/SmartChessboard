Interface Implementation
========================
In order to use the chessboard the python code needs to be able to communicate with the hardware. Since every project
will use a slightly differently hardware setup we need to configure the software. The configuration is done by implementing the
interface :class:`Hardware.HardwareInterface.HardwareInterface` in the python file **src/Hardware/HardwareImplementation.py/**
There is already a complete and extensive implementation in this file which can be used as an example. Note that functional
hardware tests are available in the `tests` directory.

Hardware interface
------------------

.. autoclass:: Hardware.HardwareInterface.HardwareInterface
    :members:
    :noindex:

The methods **mark_squares** and **get_occupancy** are abstract methods. This means that the methods are important
and always need to be implemented. The method **mark_squares** is used to mark the squares on the board and the
**get_occupancy** method returns all occupied squares. The other methods are all optional and do not need to be implemented.
A minimal example implementation can be found below. This implementation uses a very simple hardware setup and only marks
one LED per square. The hardware uses one HTK16K33 and 4 MCP23017 each connected to 16 reed switches. This is similar
to the hardware used in the original project. More information about the hardware can be found
:doc:`here <HardwareDescription>`.

.. code-block:: python

    import chess
    import board
    import busio
    import digitalio
    from adafruit_ht16k33 import matrix
    from adafruit_mcp230xx.mcp23017 import MCP23017

    class HardwareImplementation(HardwareInterface.HardwareInterface):

    def __init__(self):
        """ Set up hardware connection """
        i2c = busio.I2C(board.SCL, board.SDA)
        self._led = matrix.MatrixBackpack16x8(i2x)
        mcp = [MCP23017(i2c, address=0x20 + i) for i in range(4)]

        # Initialize reed matrix
        for file in range(8):
            for rank in range(8):
                self._board_reed[file][rank] = mcp[rank // 2].get_pin(pin_id)
                self._board_reed[file][rank].direction = digitalio.Direction.INPUT
                self._board_reed[file][rank].pull = digitalio.Pull.UP

    def mark_squares(self, squares):
        for file in range(8):
            for rank in range(8):
                self._led[file][rank] = squares[file][rank]

    def get_occupancy(self):
        result = []
        for file in self._board_reed:
            result_file = []
            for square in file:
               result_file.append(not square.value)
            result.append(result_file)
        return result

Advanced implementation resources
---------------------------------
In the git repository a complete implementation of the interface can be found. This class
:class:`Hardware.HardwareInterface.HardwareImplementation` not only implements all optional methods it also contains so
powerful ideas to improve the quality of the chess board. These ideas are more complex but understanding them can
greatly improve your software. How these ideas should be used depends on the hardware setup used. The original hardware
is described in the :doc:`hardware section <HardwareDescription>`.

The hardware uses an 8 by 16 LED matrix driver and one MCP23017 to create a 9 by 9 LED matrix. We want to highlight a square
by lighting up the 4 LEDs at the corners of a square. This adds a lot of complexity to the code which can cause errors.
This complexity can be managed by wrapping the LEDs in a a new class. Our other code can now mark squares using that new
class and all difficult code will be contained in the LED class.  In the original implementation the class
:class:`Hardware.HardwareInterface.LedWrapper` hides the complexity of the LEDs.
This class just takes an 8 by 8 matrix of squares as input and turns on the correct LEDs. Outside the class we don't
need to keep in mind how the LEDs are connected and which LEDs should be turned on or off.

Creating new classes is nice and reduces the complexity but the really important feature from the original code is the
:class:`Hardware.SafeDecorator` module. If your hardware uses the I2C bus then I strongly recommend using the safe
decorator.  The safe decorator is a complex piece of software which uses some advanced python features which new users
are unlikely to be familiar with. I strongly advice that new users thoroughly read this section.

In order to understand the safe decorator we first need to understand the problem it solves. The software communicates
with the hardware over this I2C bus. In practice this bus is often noisy. This means that certain messages from and to
the hardware might become corrupted. When a message becomes corrupted then the hardware will give an error.
If we don't do anything then this error will crash the software. In practice we know that hardware errors are almost always
caused by this noise. If the error is caused by noise then we just resend the message and ignore the error. This is
what the safe decorator does. As an example lets say that we have a hardware device *device* and we can send a message
*m* to it over the i2C bus using a *send* method. This would gives us the following simple python code.

.. code-block:: python

    device.send(m)

Unfortunately, this code would crash if the message became corrupted. What we would actually like to do is:

.. code-block:: python

    tries = 0
    while True:
        try:
            device.send(m)
            break
        except OSError:
            if tries < 3:
                tries += 1
            else:
                raise

This code tries to send the message *m* and it will continue normally after it has succeeded. However if an *OSError* is
triggered then the code will *catch* (stop) the error and try to resend the message. If the error was just caused by
some noise then it will almost always succeed within 3 tries. However, if there is another problem then resending the
message will not resolve the issue. In this case we always get an error and we can only *throw* the error. This will stop
the program and will show the user the error.

This code is great and all but it is also very large. If we write this code for every operation then the python code will
become massive and unreadable. Here is where the safe decorator comes in. The following code uses the
:class:`Hardware.SafeDecorator` to do the same but is way more compact.

.. code-block:: python

    SafeDecorator.perform_safe(device.send)(m)

The *perform_safe* function accepts a function as input and creates a function that will perform the input function safely,
ie 3 attempts will be made to execute the function. Next to this the output function accepts the
same input and returns the same output as the input function. This is great because we can now easily use the I2C bus
without worrying about noise. Note that the input of *perform_safe* needs to be a function. Sometimes you will want to
perform an operation which does not look like a function. Most python operations are secretly functions. As an example
lets say that we don't have the *device.send* function but instead need to set some variable, ie:

.. code-block:: python

    device.message = m


This does not look like a function but it actually is a function. The following line of code is exactly the same.

.. code-block:: python

    setattr(device, 'message', m)

So we can use the safe decorator to perform the assignment safely:

.. code-block:: python

    perform_safe(setattr)(device, 'message', m)

This pattern is commonly used in :class:`Hardware.HardwareInterface.HardwareImplementation`. There is always an option to
convert some line of python code to a function. If you encounter a problem finding the right function I would advice looking
at *lambdas*. Lambas are outside of the scope of this documentation but commonly used in the project.

Lastly there is one more feature in the :class:`Hardware.SafeDecorator` module which can be useful. This is the
:class:`Hardware.SafeDecorator.perform_safe_factory`. This method allows you to slightly modify the safe decorator.
In the original hardware a device TCA9548a is used. This is a device which limits the noise on the I2C bus however there is one
problem with this device. There is a bug in the device which requires you to reset the device after every error.
So we want to run the following code to safely perform an operation:

.. code-block:: python

    device.send(m)
    tries = 0
    while True:
        try:
            device.send(m)
            break
        except OSError:
        if tries < 3:
            TCA9548a.reset() # new
            tries += 1
        else:
            raise

This is where the factory comes in. The factory takes one reset function as input and then returns a safe decorator which
uses the reset function after every error. This would give us the following code (the decorator can be reused):

.. code-block:: python

    decorator = perform_safe_factory(TCA9548a.reset) # Note no brackets after TCA9548a.reset
    decorator(device.send)(m)

New python users might be unfamiliar with functions that take functions as input and return functions as output but
I hope the explanation is clear enough to start using them. The complete documentation of the :class:`Hardware.SafeDecorator` can
be found here.