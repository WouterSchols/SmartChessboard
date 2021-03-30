from chess import engine
import Hardware.PlayerClientInterface
import chess.engine


class ConsoleClient(Hardware.PlayerClientInterface.PlayerClientInterface):
    """ Defines commandline interface mainly for testing purposes """

    _board: chess.Board

    def __init__(self):
        """ Creates board """
        self._board = chess.Board()

    def get_move(self) -> chess.engine.PlayResult:
        """ Parses move """
        print(self._board)
        while True:
            txt = input()
            try:
                move = chess.Move.from_uci(txt)
                break
            except ValueError:
                print("Not parsed")
        self._board.push(move)
        return engine.PlayResult(move, None)

    def set_move(self, move: chess.engine.PlayResult):
        """ Report new moveto client """
        if move.move is not None:
            self._board.push(move.move)
