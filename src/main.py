from Clients import EngineClient, ConsoleClient, ChessDotComClient, HardwareClient
import chess
from typing import List, Any
import setuptools


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    white = HardwareClient.HardwareClient()
    black = ChessDotComClient.ChessDotComClient()
    while True:
        black.set_move(white.get_move())
        white.set_move(black.get_move())


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
