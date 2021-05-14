from abc import ABC, abstractmethod
import chess.engine
import chess
from datetime import timedelta
from typing import Dict, Optional, Tuple


class ClientInterface(ABC):
    """ Defines interface of a client """

    _board: chess.Board  # The chess board
    _resigned: bool  # Flag if client has resigned, needs to be set to true if the client resigns
    color: chess.Color  # The player color
    # Shared metadata between clients, used to store additional game info, usage is optional, avoid making assumptions
    # about the metadata content
    metadata: Dict[str, str] = {}

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

    def __init__(self, color: chess.Color):
        """ Initializes the client

        :param color: Sets color of the board
        """
        self._board = chess.Board()
        self._resigned = False
        self.color = color
        key = ("white" if self.color else "black") + "_name"
        if key not in self.metadata:
            self.metadata[key] = type(self).__name__

    def game_is_over(self) -> bool:
        """ Checks if game is over

        Implementations of PlayerClientInterface can choose to extend this method to display the result,
        accept resignation or accept draw offers

        :return: Returns True iff game is over
        """
        return self._board.is_game_over() or self._resigned

    def synchronize_clocks(self, clock: Optional[Tuple[timedelta, timedelta]] = None) \
            -> Optional[Tuple[timedelta, timedelta]]:
        """ Synchronize clocks between two clients

        :param clock: Input clock from the other client (white time, black time)
        :return: return clock from current client (white time, black time) if available
        """
        return clock
