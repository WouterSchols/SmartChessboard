from abc import ABC, abstractmethod
from typing import List


class HardwareInterface(ABC):
    """ Defines interface to the hardware """

    @abstractmethod
    def mark_squares(self, square: List[List[bool]]):
        """ Marks square[x,y] on the chessboard 0 <= x, y < 8 if square[x,y] == True"""
        pass

    @abstractmethod
    def get_occupancy(self) -> List[List[bool]]:
        """ Returns all occupied squares """
        pass
