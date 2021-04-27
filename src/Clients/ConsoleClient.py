from chess import engine
from Clients import ClientInterface
import chess.engine


class ConsoleClient(ClientInterface.ClientInterface):
    """ Defines commandline interface mainly for testing purposes """

    def get_move(self) -> chess.engine.PlayResult:
        """ Parses new move <from_square><to_square> or resign

        Prints the current position and waits for an input move.
        Input move should be in format <from_square><to_square> ie. e2e4 to move pawn to e4. The move should be
        legal in the current position
        :returns: Move played in engine plays format
        """
        print(self._board)
        while True:
            txt = input("Set move:")
            txt = txt.replace(" ", "")
            draw = False
            if txt == "resign":
                self._resigned = True
                return engine.PlayResult(None, None, resigned=True)
            if "draw" in txt:
                draw = True
                txt = txt.replace("draw", "")
            try:
                move = chess.Move.from_uci(txt)
                if move in self._board.legal_moves:
                    break
                else:
                    print("not a legal move")
            except ValueError:
                print("Not parsed")
        self._board.push(move)
        return engine.PlayResult(move, None, draw_offered=draw)

    def set_move(self, move: chess.engine.PlayResult):
        """ Report new move to the client
        :param move: opponents move in engine format, only move field is used
        """
        if not move.resigned:
            print("player resigned")
        if move.move is not None:
            self._board.push(move.move)
            if move.draw_offered:
                print("Draw offered")
