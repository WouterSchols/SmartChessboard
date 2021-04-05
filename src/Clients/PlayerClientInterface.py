from abc import ABC, abstractmethod
import chess.engine


class PlayerClientInterface(ABC):
    """ Defines interface of a client """

    @abstractmethod
    def get_move(self) -> chess.engine.PlayResult:
        """ Returns next move from client
        :returns: next move played by the client in the normal engine output format
        """
        pass

    @abstractmethod
    def set_move(self, move: chess.engine.PlayResult) -> None:
        """ Report new move to client
        :param move: reports move of opponent to client using normal engine output format
        """
        pass
