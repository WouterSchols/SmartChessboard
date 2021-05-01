from time import sleep
import sys
import os.path
from Hardware.HardwareInterface import Offer
import chess

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), os.path.pardir)))
print(sys.path)

from src.Hardware.HardwareImplementation import HardwareImplementation


def mark_test():
    """ Marks a square on the chessboard from command prompt"""
    hi = HardwareImplementation()
    while True:
        inp = input("Mark square: ")
        if len(inp) == 2:
            matrix = [[False]*8 for _ in range(8)]
            matrix[ord(inp[0]) - ord('a')][int(inp[1]) - 1] = True
            #print("file " + str(ord(inp[0]) - ord('a')) + ", " + (int(inp[1] - 1)))
            hi.mark_squares(matrix)
        sleep(1)


def detect_test():
    """ Detects an occupied square and writes it on the chessboard"""
    hi = HardwareImplementation()
    while True:
        matrix = hi.get_occupancy()
        for file in range(8):
            for rank in range(8):
                if matrix[file][rank]:
                    print(chr(ord('a') + file) + str(rank + 1))
        sleep(1)


def detect_and_mark_test():
    """ Detects occupancy and marks occupied squares """
    hi = HardwareImplementation()
    while True:
        hi.mark_squares(hi.get_occupancy())
        sleep(1)

def promote_test():
    """ Detects promotion """
    hi = HardwareImplementation()
    while True:
        piece = hi.promotion_piece()
        print(chess.piece_name(piece))
        sleep(1)

def game_end_offers():
    """ Detects resignation and draw offers """
    hi = HardwareImplementation()
    while True:
        offer = hi.game_end_offers()
        if offer is offer.CONTINUE:
            print("continue")
        elif offer is offer.DRAW:
            print("draw")
        else:
            print("resignation")
        sleep(1)

if __name__ == "__main__":
    print("1. mark_test")
    print("2. detect_test")
    print("3. detect_and_mark_test")
    print("4. promote_test")
    print("5. game_end_offers")
    print('-'*20)
    inp = input("choice (1, 2, 3, 4, 5): ")
    if int(inp) == 1:
        mark_test()
    if int(inp) == 2:
        detect_test()
    if int(inp) == 3:
        detect_and_mark_test()
    if int(inp) == 4:
        promote_test()
    if int(inp) == 3:
        game_end_offers()
