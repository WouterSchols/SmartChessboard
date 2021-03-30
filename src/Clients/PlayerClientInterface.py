from abc import ABC, abstractmethod
import chess.engine


class PlayerClientInterface(ABC):
    """ Defines interface of a client """

    @abstractmethod
    def get_move(self) -> chess.engine.PlayResult:
        """ Returns next move from client"""
        pass

    @abstractmethod
    def set_move(self, move: chess.engine.PlayResult):
        """ Report new move to client """
        pass
