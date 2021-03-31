from src.Hardware import HardwareInterface
from typing import List
import board
import busio
import digitalio
import adafruit_tca9548a
from adafruit_ht16k33 import matrix
from adafruit_mcp230xx.mcp23017 import MCP23017

TRIES = 5

class HardwareImplementation(HardwareInterface.HardwareInterface):
    """ Interface to Hardware chessboard"""

    def __init__(self):
        """ Set up hardware connection """
        i2c = busio.I2C(board.SCL, board.SDA)
        tca = adafruit_tca9548a.TCA9548A(i2c, address=0x71)
        mcp = [MCP23017(tca[i], address=0x20) for i in range(4)]

        self._board_reed = [[], [], [], [], [], [], [], []]

        # Maps reed switches to board
        for mcp_id in range(4):
            # Map first rank from a to h
            for file in range(8):
                self._board_reed[mcp_id * 2].append(mcp[mcp_id].get_pin(file))  # Which MCP to use
                self._board_reed[mcp_id * 2][-1].direction = digitalio.Direction.INPUT  # Set pin to input
                self._board_reed[mcp_id * 2][-1].pull = digitalio.Pull.UP  # Turn on resistor

            # Map second rank h to a
            for file in reversed(range(8)):
                self._board_reed[mcp_id * 2 + 1].append(mcp[mcp_id].get_pin(file))  # Which MCP to use
                self._board_reed[mcp_id * 2 + 1][-1].direction = digitalio.Direction.INPUT  # Set pin to input
                self._board_reed[mcp_id * 2 + 1][-1].pull = digitalio.Pull.UP  # Turn on resistor

        # for file in range(0, 8):
        #     for rank in range(0, 8):
        #         pinId = 7 - rank if file % 2 == 0 else 8 + rank  # Which MCP pin to use (even rows 0
        #         self._board_reed[file].append(mcp[file // 2].get_pin(pinId))  # Which MCP to use
        #         self._board_reed[i][j].direction = digitalio.Direction.INPUT
        #         self._board_reed[i][j].pull = digitalio.Pull.UP

        # Initialize LED matrix
        self._led_matrix = LedWrapper(matrix.MatrixBackpack16x8(tca[4]),
                                           MCP23017(tca[5], address=0x20))
        self._led_matrix.clear()

    def mark_squares(self, matrix: List[List[bool]]):
        """ Marks square[file][rank] on the chessboard 0 <= file, column < 8 if square[file][rank] == True"""
        self._led_matrix.clear()
        for file in range(8):
            for rank in range(8):
                if matrix[file][rank]:
                    self._led_matrix.mark_square(file, rank)

    def get_occupancy(self) -> List[List[bool]]:
        """ Returns all occupied squares """
        result = []
        for file in self._board_reed:
            result_file = []
            for square in file:
                try:
                    result_file.append(not square.value)  # Check if square is not free
                except OSError:  # OSError commonly caused by noise on the I2C buss
                    res = retry(result.append, square.value)
                    if not res:
                        raise
            result.append(result_file)
        return result


class LedWrapper:
    """" Wraps LED hardware """

    def __init__(self, matrix: matrix.MatrixBackpack16x8, mcp: MCP23017):
        self._matrix = matrix
        self._column = [mcp.get_pin(i) for i in range(0, 9)]
        for pin in self._column:
            try:
               pin.direction = digitalio.Direction.OUTPUT
            except OSError:
                res = retry(setattr, pin, 'direction', Direction.OUTPUT)
                if not res:
                    raise
            try:
               pin.value = False
            except OSError:
                res = retry(setattr, pin, 'value', False)
                if not res:
                    raise
        self.clear()

    def clear(self):
        """ Clears all square on the chessboard """
        try:
            self._matrix.fill(0)
        except OSError:  # OSError commonly caused by noise on the I2C buss
            res = retry(self._matrix.fill, 0)
            if not res:
                raise
        for led in self._column:
            try:
                led.value = False
            except OSError:
                res = retry(setattr, led, 'value', False)
                if not res:
                    raise

    def mark_square(self, file: int, rank: int):
        """ Marks one square on the chessboard"""
        if file == 0:
            try:
                self._column[8 - rank].value = True
            except OSError:
                res = retry(setattr, self._column[8 - rank], 'value', True)
                if not res:
                    raise
            try:
                self._column[7 - rank].value = True
            except OSError:
                res = retry(setattr, self._column[7 - rank], 'value', True)
                if not res:
                    raise
        else:
            try:
                self._matrix[7 - rank, file - 1] = True
                self._matrix[7 - rank + 1, file - 1] = True
            except OSError:
                tries = 0
                while tries < TRIES:
                    try:
                        self._matrix[7 - rank, file - 1] = True
                        self._matrix[7 - rank + 1, file - 1] = True
                        break
                    except OSError:
                        tries += 1
                if tries >= TRIES:
                    raise
        try:
            self._matrix[7 - rank, file] = True
            self._matrix[7 - rank + 1, file] = True
        except OSError:
            tries = 0
            while tries < TRIES:
                try:
                    self._matrix[7 - rank, file] = True
                    self._matrix[7 - rank + 1, file] = True
                    break
                except OSError:
                    tries += 1
            if tries >= TRIES:
                raise


def retry(func, *arg) -> bool:
    """" Tries to execute a function until no exception is thrown or 3 tries have failed """
    tries = 0
    while tries < TRIES:
        try:
            func(*arg)
            return True
        except OSError:
            tries += 1
    return False
