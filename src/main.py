from src.Clients import EngineClient, HardwareClient
import chess


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    p1 = HardwareClient.HardwareClient(chess.WHITE)
    p2 = EngineClient.EngineClient()
    while True:
        p2.set_move(p1.get_move())
        p1.set_move(p2.get_move())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
