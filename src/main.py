from src.Clients import EngineClient, ConsoleClient
# import chess
from typing import List, Any
import setuptools

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # white = ConsoleClient.ConsoleClient()
    # black = EngineClient.EngineClient()
    # while True:
    #     black.set_move(white.get_move())
    #     white.set_move(black.get_move())
    print(setuptools.find_packages(where="src",
                                      include=['Clients']))

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
