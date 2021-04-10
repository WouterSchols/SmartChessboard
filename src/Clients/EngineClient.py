from src.Clients import PlayerClientInterface
import chess.engine


class EngineClient(PlayerClientInterface.PlayerClientInterface):
    """ Defines interface for an engine """

    _board: chess.Board
    _engine: chess.engine

    def __init__(self):
        """ Creates engine, binary should be at BinaryDependencies/Engine/stockfish.exe """
        # self._engine = chess.engine.SimpleEngine.popen_uci("Engine/BinaryDependencies.exe")
        self._engine = chess.engine.SimpleEngine.popen_uci("../BinaryDependencies/Engines/stockfish.exe")
        self._board = chess.Board()

    def __del__(self):
        """" Terminates engine """
        self._engine.quit()

    def get_move(self) -> chess.engine.PlayResult:
        """ Returns next move from client """
        move = self._engine.play(self._board, chess.engine.Limit(time=0.1))
        self._board.push(move.move)
        return move

    def set_move(self, move: chess.engine.PlayResult):
        """ Report new move to client """
        if move.move is not None:
            self._board.push(move.move)
