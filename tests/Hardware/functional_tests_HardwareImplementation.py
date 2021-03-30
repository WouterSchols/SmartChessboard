from time import sleep
from src.Hardware.HardwareImplementation import HardwareImplementation

if __name__ == "__main__":
    print("test")


def mark_test():
    """ Marks a square on the chessboard from command prompt"""
    hi = HardwareImplementation()
    while True:
        inp = input("Mark square: ")
        if len(inp) == 2:
            matrix = [[False]*8 for _ in range(8)]
            matrix[ord(inp[0]) - ord('a')][int(inp[1])] = True
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
                    print(chr(ord('a') + file) + str(rank))
        sleep(1)


def detect_and_mark_test():
    """ Detects occupancy and marks occupied squares """
    hi = HardwareImplementation.HardwareImplementation()
    while True:
        hi.mark_squares(hi.get_occupancy())
        sleep(1)
