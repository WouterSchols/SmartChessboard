from Hardware import HardwareInterface
from typing import List, Any, Callable
import board
import busio
import digitalio
import adafruit_tca9548a
from adafruit_ht16k33 import matrix
from adafruit_mcp230xx.mcp23017 import MCP23017


def perform_safe(func: Callable[[Any], Any], max_tries: int = 5, reset: Callable[[None], None] = None) \
        -> Callable[[Any], Any]:
    """" Tries to execute func(*args) until no OSError is thrown or TRIES attempts have failed

    The i2c buss is sensitive to noise. Corrupted messages can trigger an OSError on the buss device.
    We can recover from this error by simply resending the message until it arrives correctly. This method accepts
    a function func which could trigger an OSError which would cause the program to fail.
    We can easily recover from this error by retrying 'func' if the error is cause by noise. The perform
    safe decorator makes sure that an error is only trow if the operation fails max_tries times
    :param func: function to be executed
    :param max_tries: maximum amount that func will be attempted
    :return: function which executes func untill it either succeeds or max_tries attempts have failed
    :rtype: Same as func
    """

    def safe_wrapper(*args, **kwargs):
        tries = 0
        while True:
            try:
                return func(*args, **kwargs)
            except OSError:
                if tries < max_tries:
                    tries += 1
                    if reset is not None:
                        reset()
                else:
                    raise

    return safe_wrapper


class HardwareImplementation(HardwareInterface.HardwareInterface):
    """ Interface to Hardware chessboard"""

    def __init__(self):
        """ Set up hardware connection

        Sets up connections to the following bus devices over the i2c bus:
        - Sets up a TCA9548a to handle the high traffic load on the bus
        - Sets up a 8x8 reed_matrix mapped trough 4 MCP23017
        - Sets up a 9x9 led_matrix with the interface LedWrapper which uses a HT16k33 and 1 MCP23017
        """
        self._led_wrapper = None
        self._link_hardware()

    @perform_safe
    def _link_hardware(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        tca = adafruit_tca9548a.TCA9548A(i2c, address=0x71)
        mcp = [MCP23017(tca[i], address=0x20) for i in range(4)]
        self._board_reed = [[] for _ in range(8)]

        # Maps reed switches to board
        for mcp_id in range(4):
            # Map first, third, fifth, seventh rank from a to h
            for file in range(8):
                self._board_reed[mcp_id * 2].append(mcp[mcp_id].get_pin(file))  # Which MCP to use
                # Set pin to input and turn on resistor
                self._board_reed[mcp_id * 2][-1].direction = digitalio.Direction.INPUT
                self._board_reed[mcp_id * 2][-1].pull = digitalio.Pull.UP

            # Map second, fourth, sixth, eight rank h to a (h to a was easier to wire in hardware)
            for file in reversed(range(8)):
                self._board_reed[mcp_id * 2 + 1].append(mcp[mcp_id].get_pin(file))  # Which MCP to use
                self._board_reed[mcp_id * 2 + 1][-1].direction = digitalio.Direction.INPUT
                self._board_reed[mcp_id * 2 + 1][-1].pull = digitalio.Pull.UP

        # Initialize LED matrix
        if self._led_wrapper is None:
            self._led_wrapper = LedWrapper(matrix.MatrixBackpack16x8(tca[4]), MCP23017(tca[5], address=0x20)
                                           , self._link_hardware)
        else:
            self._led_wrapper.link_led(matrix.MatrixBackpack16x8(tca[4]), MCP23017(tca[5], address=0x20))


    def mark_squares(self, squares: List[List[bool]]) -> None:
        """ Marks squares on the chessboard where squares is an 8x8 matrix implemented as a 2s list

        Note that squares are mapped as squares[file][rank] ie. a1 = squares[0][0], a2 = squares[0][1],
          b1 = squares[1][0] and h8 = squares[7][7]
        :param squares: 8x8 matrix of squares to mark on the chessboard where square [file][rank]
            is marked if square[file][rank] == TRUE
        """
        self._led_wrapper.clear()
        for file in range(8):
            for rank in range(8):
                if squares[file][rank]:
                    self._led_wrapper.mark_square(file, rank)

    def get_occupancy(self) -> List[List[bool]]:
        """ Returns all occupied squares as 8x8 matrix implemented as a 2d list

        Note that squares are mapped as squares[file][rank] so if square a2 is occupied then
            get_occupancy[0][1] == TRUE
        :return: 8x8 matrix with all occupied squares on the chessboard
        """
        result = []
        for file in self._board_reed:
            result_file = []
            for square in file:
                result += not perform_safe(getattr, reset=_link_hardware)(square, 'value')  # result += [not square.value]
            result.append(result_file)
        return result


class LedWrapper:
    """" Wraps LED hardware """

    def __init__(self, ht16k33: matrix.MatrixBackpack16x8, mcp: MCP23017, reset: Callable[[None], None]):
        """ Initializes the led matrix using the ht16k33 and MCP23017

        :param ht16k33: ht16k33 instance controlling a 8x9 led matrix
        :param mcp: MCP23017 instance controlling the left most row of LED
        """
        self._reset = reset
        self.link_led(ht16k33, mcp)
        self.clear()

    def link_led(self, ht16k33: matrix.MatrixBackpack16x8, mcp: MCP23017):
        self._ht16k33 = ht16k33
        self._column = [mcp.get_pin(i) for i in range(9)]
        for pin in self._column:
            perform_safe(setattr, reset=self._reset)(pin, 'direction', digitalio.Direction.OUTPUT)  # pin.direction = OUTPUT

    def clear(self):
        """ Clears all square on the chessboard """
        perform_safe(self._ht16k33.fill, reset=self._reset)(0)  # squares.fill(0)
        for led in self._column:
            perform_safe(setattr, reset=self._reset)(led, 'value', False)  # led.value = False

    def mark_square(self, file: int, rank: int):
        """ Marks one square on the chessboard """

        def light(rank, file):
            """ Safely turns on LED at position rank, file """
            self._ht16k33[rank, file] = True

        if file == 0:
            perform_safe(setattr, reset=self._reset)(self._column[8 - rank], 'value', True)  # _column[8 - rank].value = True
            perform_safe(setattr, reset=self._reset)(self._column[7 - rank], 'value', True)  # _column[7 - rank].value = True
        else:
            perform_safe(light, reset=self._reset)(8 - rank, file - 1)  # _ht16k33[7 - rank][file - 1]=True
            perform_safe(light, reset=self._reset)(7 - rank, file - 1)  # _ht16k33[6 - rank][file - 1]=True
        perform_safe(light, reset=self._reset)(8 - rank, file)  # _ht16k33[7 - rank][file] = True
        perform_safe(light, reset=self._reset)(7 - rank, file)  # _ht16k33[6 - rank][file] = True
