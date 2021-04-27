from Clients import ClientInterface
import chess.engine


class EngineClient(ClientInterface.ClientInterface):
    """ Defines interface for an engine """

    _engine: chess.engine

    def __init__(self, color: chess.Color, path: str, move_time=0.1):
        """ Creates engine, binary should be at BinaryDependencies/Engine/stockfish.exe
        :param color: Color to initialize the client
        :param path: The path to the engine
        :param move_time: The amount of time the engine has to move
        """
        super().__init__(color)
        self._engine = chess.engine.SimpleEngine.popen_uci(path)
        self.move_time = move_time

    def __del__(self):
        """" Terminates engine """
        if hasattr(self, '_engine'):
            self._engine.quit()

    def get_move(self) -> chess.engine.PlayResult:
        """ Returns next move from client """
        move = self._engine.play(self._board, chess.engine.Limit(time=self.move_time))
        self._board.push(move.move)
        self._resigned = move.resigned
        return move

    def set_move(self, move: chess.engine.PlayResult):
        """ Report new move to client """
        if move.move is not None:
            print(self._board)
            self._board.push(move.move)
