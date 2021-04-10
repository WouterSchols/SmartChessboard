from src.Clients import EngineClient, ConsoleClient, ChessDotComClient
import chess
from typing import List, Any, Callable
import setuptools

class A:
    val = 1

class B:
    a = A()

def set(a, val):
    a.val = val

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # white = ConsoleClient.ConsoleClient()
    # black = ChessDotComClient.ChessDotComClient(chess.BLACK)
    # while True:
    #     black.set_move(white.get_move())
    #     white.set_move(black.get_move())
    b = B()
    print(b.a.val)
    set(b.a, 2)
    print(b.a.val)


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
