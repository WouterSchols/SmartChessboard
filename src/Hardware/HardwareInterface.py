from abc import ABC, abstractmethod
from typing import List
from enum import Enum
import chess


class Offer(Enum):
    CONTINUE = 0
    DRAW = 1
    RESIGN = 2


class HardwareInterface(ABC):
    """ Defines interface to the hardware """

    @abstractmethod
    def mark_squares(self, squares: List[List[bool]]) -> None:
        """ Marks squares on the chessboard where squares is an 8x8 matrix implemented as a 2s list

        Note that squares are mapped as squares[file][rank] ie. a1 = squares[0][0], a2 = squares[0][1],
        b1 = squares[1][0] and h8 = squares[7][7]

        :param squares: 8x8 matrix of squares to mark on the chessboard where square [file][rank] \
        is marked if square[file][rank] == TRUE
        """
        pass

    @abstractmethod
    def get_occupancy(self) -> List[List[bool]]:
        """ Returns all occupied squares as 8x8 matrix implemented as a 2d list

        Note that squares are mapped as squares[file][rank] so if square a2 is occupied then
        get_occupancy[0][1] equals TRUE
        :return: 8x8 matrix with all occupied squares on the chessboard
        """
        pass

    def promotion_piece(self) -> chess.Piece:
        """ Which piece to promote to

        :return: Piece to promote to if not reimplemented returns queen
        """
        return chess.QUEEN

    def game_end_offers(self) -> Offer:
        """ Returns continue, draw or return offers

        :return: Always returns continue
        """
        return Offer.CONTINUE

    def display(self, txt: str):
        """ Displays text string on hardware

        :param txt: text to display on hardware
        """
        print(txt)
        pass
