import chess
from Hardware import HardwareInterface, safe_decorator
from typing import List, Any, Callable, Dict
import board
import busio
import digitalio
import adafruit_tca9548a
from adafruit_ht16k33 import matrix
from adafruit_mcp230xx.mcp23017 import MCP23017


class HardwareImplementation(HardwareInterface.HardwareInterface):
    """ Interface to Hardware chessboard"""

    _board_reed = [[None]*8 for _ in range(8)]
    _perform_safe: Callable[[Callable[[Any], Any]], Callable[[Any], Any]]

    def __init__(self):
        """ Set up hardware connection

        Sets up connections to the following bus devices over the i2c bus:
        - Sets up a TCA9548a to handle the high traffic load on the bus
        - Sets up a 8x8 reed_matrix mapped trough 4 MCP23017
        - Sets up a 9x9 led_matrix with the interface LedWrapper which uses a HT16k33 and 1 MCP23017
        """
        i2c = busio.I2C(board.SCL, board.SDA)
        tca = adafruit_tca9548a.TCA9548A(i2c, address=0x71)
        self._perform_safe = safe_decorator.perform_safe_factory(setattr(tca.i2c, '_reset', False))

        mcp = [self._perform_safe(lambda i: MCP23017(tca[i], address=0x20))(i) for i in range(4)]

        # Initialize reed matrix
        for file in range(8):
            for rank in range(8):
                pinId = file if rank % 2 == 0 else 15 - file
                self._board_reed[file][rank] = self._perform_safe(mcp[rank // 2].get_pin)(pinId)
                self._perform_safe(setattr)(self._board_reed[file][rank], "direction", digitalio.Direction.INPUT)
                self._perform_safe(setattr)(self._board_reed[file][rank], "pull", digitalio.Pull.UP)

        # Map output buttons
        self._buttons = []
        for pinId in range(8, 13):
            self._buttons.append(self._perform_safe(mcp[6].get_pin)(pinId))
            self._perform_safe(setattr)(self._buttons[-1], "direction", digitalio.Direction.INPUT)
            self._perform_safe(setattr)(self._buttons[-1], "pull", digitalio.Pull.UP)


        # Initialize LED matrix
        self._led_wrapper = LedWrapper(matrix.MatrixBackpack16x8(tca[4]),
                                      MCP23017(tca[5], address=0x20), self._perform_safe)
        self._led_wrapper.clear()

    def __del__(self):
        """ Turn of LED before shutting down """
        self._led_wrapper.clear()

    def mark_squares(self, squares: List[List[bool]]) -> None:
        """ Marks squares on the chessboard where squares is an 8x8 matrix implemented as a 2s list

        Note that squares are mapped as squares[file][rank] ie. a1 = squares[0][0], a2 = squares[0][1],
          b1 = squares[1][0] and h8 = squares[7][7]
        :param squares: 8x8 matrix of squares to mark on the chessboard where square [file][rank]
            is marked if square[file][rank] == TRUE
        """
        self._led_wrapper.set_squares(squares)

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
                result_file.append(not self._perform_safe(getattr)(square, 'value'))  # result += [not square.value]
            result.append(result_file)
        return result

    def promotion_piece(self) -> chess.Piece:
        """ Which piece to promote to
            Reads input button to select promotion piece, writes selected piece to display and waits for confirmation
        :return: Piece to promote to
        """
        piece = chess.QUEEN
        while True:
            if self._perform_safe(getattr)(self._buttons[0], 'value'):
                piece = chess.QUEEN

            if self._perform_safe(getattr)(self._buttons[1], 'value'):
                piece = chess.ROOK

            if self._perform_safe(getattr)(self._buttons[2], 'value'):
                piece = chess.BISHOP

            if self._perform_safe(getattr)(self._buttons[3], 'value'):
                piece = chess.KNIGHT

            self.display(chess.piece_name(piece))
            if self._perform_safe(getattr)(self._buttons[4], 'value'):
                return piece

    def game_end_offers(self) -> HardwareInterface.Offer:
        """ Returns continue, draw or return offers
            If no button pressed returns continue, otherwise wait for confirmation
        :return: Always returns continue
        """
        if self._perform_safe(getattr)(self._buttons[0], 'value'):
            while True:
                if self._perform_safe(getattr)(self._buttons[4], 'value'):
                    return HardwareInterface.Offer.RESIGN
                if self._perform_safe(getattr)(self._buttons[3], 'value'):
                    return HardwareInterface.Offer.CONTINUE
        if self._perform_safe(getattr)(self._buttons[1], 'value'):
            while True:
                if self._perform_safe(getattr)(self._buttons[4], 'value'):
                    return HardwareInterface.Offer.DRAW
                if self._perform_safe(getattr)(self._buttons[3], 'value'):
                    return HardwareInterface.Offer.DRAW
        return HardwareInterface.Offer.CONTINUE



class LedWrapper:
    """" Wraps LED hardware """

    def __init__(self, ht16k33: matrix.MatrixBackpack16x8, mcp: MCP23017, perform_safe):
        """ Initializes the led matrix using the ht16k33 and MCP23017

        :param ht16k33: ht16k33 instance controlling a 8x9 led matrix
        :param mcp: MCP23017 instance controlling the left most row of LED
        """
        self._ht16k33 = ht16k33
        self._perform_safe = perform_safe
        self._column = [self._perform_safe(lambda i: mcp.get_pin(i))(i) for i in range(0, 9)]
        for pin in self._column:
            self._perform_safe(setattr)(pin, 'direction', digitalio.Direction.OUTPUT)  # pin.direction = OUTPUT
            self._perform_safe(setattr)(pin, 'value', False)  # pin.value = False
        self.clear()

    def clear(self):
        """ Clears all square on the chessboard """
        self._perform_safe(self._ht16k33.fill)(0)  # squares.fill(0)
        for led in self._column:
            self._perform_safe(setattr)(led, 'value', False)  # led.value = False

    def set_squares(self, squares: List[List[bool]]):
        """ Marks squares on the chessboard

        Improvement on calling clear() then marking all squires since this prevents a flickering of the LED
        :param squares: 8x8 matrix with the squares to be marked
        """

        def set_LED(rank, file, val):
            """ Safely turns on LED at position rank, file """
            self._ht16k33[rank, file] = val

        for file in range(9):
            for rank in range(9):
                # Check of LED should be turned on
                value = False
                if file > 0 and rank > 0:
                    value = squares[file - 1][rank - 1]
                if not value and file < 8 and rank > 0:
                    value = squares[file][rank - 1]
                if not value and file > 0 and rank < 8:
                    value = squares[file - 1][rank]
                if not value and file < 8 and rank < 8:
                    value = squares[file][rank]

                # Turn LED on or off
                if file == 0:
                    self._perform_safe(setattr)(self._column[8 - rank], 'value', value)  # _column[8 - rank].value = True
                else:
                    self._perform_safe(set_LED)(8 - rank, file - 1, value)  # _ht16k33[7 - rank][file - 1]=True
