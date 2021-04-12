from chess import engine
from Clients import PlayerClientInterface
import chess.engine


class ConsoleClient(PlayerClientInterface.PlayerClientInterface):
    """ Defines commandline interface mainly for testing purposes """

    _board: chess.Board

    def __init__(self):
        """ Initializes board """
        self._board = chess.Board()

    def get_move(self) -> chess.engine.PlayResult:
        """ Parses new move

        Prints the current position and waits for an input move.
        Input move should be in format <from_square><to_square> ie. e2e4 to move pawn to e4. The move should be
        legal in the current position
        :returns: Move played in engine plays format
        """
        print(self._board)
        while True:
            txt = input()
            try:
                move = chess.Move.from_uci(txt)
                if move in self._board.legal_moves:
                    break
                else:
                    print("not a legal move")
            except ValueError:
                print("Not parsed")
        self._board.push(move)
        return engine.PlayResult(move, None)

    def set_move(self, move: chess.engine.PlayResult):
        """ Report new move to the client
        :param move: opponents move in engine format, only move field is used
        """
        if move.move is not None:
            self._board.push(move.move)
