import chess
from Clients import ConsoleClient, ClientInterface
from GUI import gui
try:
    from Clients import HardwareClient
    successful_import = True
except NotImplementedError:
    print("Platform not compatible with hardware client using console client")
    successful_import = False


def play(white: ClientInterface.ClientInterface, black: ClientInterface.ClientInterface):
    """ Starts a game between two clients reuses a client if possible to start a new game """
    print(f"Game started: white {type(white).__name__}, black {type(black).__name__}")
    for key in white.metadata:
        print(key + " : " + white.metadata[key])
    while True:
        black.set_move(white.get_move())
        if white.game_is_over():
            break
        white.set_move(black.get_move())
        if black.game_is_over():
            break

    # If a client is reusable reuse it (assumes hardware client is not reusable)
    if callable(getattr(white, "start_new_game", None)) or callable(getattr(black, "start_new_game", None)):
        new_opponent = white if callable(getattr(white, "start_new_game", None)) else black
        new_opponent.start_new_game()
        new_player = HardwareClient.HardwareClient(not black.color) if successful_import else \
            ConsoleClient.ConsoleClient(not black.color)
        if black.color:
            play(new_opponent, new_player)
        else:
            play(new_player, new_opponent)


if __name__ == '__main__':
    while True:
        opponent = gui.get_opponent_from_gui()
        if opponent is None:
            break
        if opponent.color is chess.WHITE:
            player = HardwareClient.HardwareClient(chess.BLACK) if successful_import else \
                ConsoleClient.ConsoleClient(chess.BLACK)
            play(opponent, player)
        else:
            player = HardwareClient.HardwareClient(chess.WHITE) if successful_import else \
                ConsoleClient.ConsoleClient(chess.WHITE)
            play(player, opponent)
