import threading
from threading import Lock
from Clients import PlayerClientInterface
import chess
from chess import engine
from Hardware import HardwareImplementation
from Hardware import HardwareInterface
from time import sleep
from typing import List, Optional
from copy import deepcopy

SLEEP_TIME = 0.5  # Time to sleep after every scan in seconds


def _get_square_from_matrix(matrix: List[List[bool]], square: chess.Square) -> bool:
    """ Get square from 8x8 matrix """
    return matrix[chess.square_file(square)][chess.square_rank(square)]


class HardwareClient(PlayerClientInterface.PlayerClientInterface):
    """ Interface to Hardware chessboard"""

    # Board state
    _board: chess.Board = chess.Board()
    _board_lock: Lock = Lock()  # Required to access _board
    _color: chess.Color

    # Input output variables
    _input_playResult: Optional[chess.engine.PlayResult] = None
    _output_playResult: Optional[chess.engine.PlayResult] = None
    _playResult_lock: Lock = Lock()  # Required to access input or output

    # Client to the HardwareInterface
    _hw_thread: threading.Thread
    _hwi: HardwareInterface = HardwareImplementation.HardwareImplementation()
    _stop_flag: bool = False
    _flag_lock: Lock = Lock()

    def __init__(self, color: chess.Color):
        """ Creates client and starts thread to control hardware chessboard """
        self._color = color
        self._hw_thread = threading.Thread(target=self._hw_control)
        self._hw_thread.start()

    def __del__(self):
        """" Terminates hardware thread and waits for thread to terminate """
        with self._flag_lock:
            self._stop_flag = True
        self._hw_thread.join()

    def get_move(self) -> chess.engine.PlayResult:
        """ Returns next move from client"""
        with self._playResult_lock:
            res = self._output_playResult
            self._output_playResult = None
        return res

    def set_move(self, move: chess.engine.PlayResult):
        """ Report new move to client """
        with self._playResult_lock:
            self._input_playResult = deepcopy(move)

    def _hw_control(self):
        """ Controls the hardware and maintains the hardware state"""
        while not self._game_is_over():
            case = -1
            with self._board_lock:
                if self._board.turn == self._color:
                    case = 0
            if case == -1:  # If statement prevents code from requesting a second lock
                with self._playResult_lock:
                    case = 1 if self._input_playResult is None else 2

            # Switch case
            if case == 0:
                self._hw_detect_player_move()
            elif case == 1:
                self._hw_wait_move_opponent()
            elif case == 2:
                self._hw_play_move_opponent()
            else:
                raise Exception("internal error")

    def _hw_detect_player_move(self):
        """ Detect move from player """
        while not self._game_is_over():
            occupancy = self._hwi.get_occupancy()
            diff = self._diff_occupancy_board(occupancy)
            self._hwi.mark_squares(diff)

            # Detect all changed squares
            squares = []
            for file in range(8):
                for rank in range(8):
                    if diff[file][rank]:
                        squares += [chess.square(file, rank)]

            if len(squares) == 2:  # Try to convert changed squares to legal move
                with self._board_lock:  # Promotion not implemented
                    if self._board.piece_at(squares[0]) is not None and \
                            self._board.piece_at(squares[0]).color == self._color:
                        move = chess.Move(squares[0], squares[1])
                    elif self._board.piece_at(squares[1]) is not None and \
                            self._board.piece_at(squares[1]).color == self._color:
                        move = chess.Move(squares[1], squares[0])
                    else:
                        continue
                    if self._board.piece_at(move.from_square).piece_type == chess.PAWN and \
                            ((self._color == chess.WHITE and chess.square_rank(move.to_square) == 7) or
                             (self._color == chess.BLACK and chess.square_rank(move.to_square) == 0)):
                        move.promotion = chess.QUEEN  # TODO change from auto promote queen
                    move_is_legal = move in self._board.legal_moves  # save result to not use two locks
                if move_is_legal:
                    with self._playResult_lock:
                        self._output_playResult = engine.PlayResult(move, None)
                    return
            sleep(SLEEP_TIME)

    def _hw_wait_move_opponent(self):
        """ Let hardware wait for opponent move"""
        while not self._game_is_over():
            with self._playResult_lock:
                if self._input_playResult is not None:
                    return
            occupancy = self._hwi.get_occupancy()
            self._hwi.mark_squares(self._diff_occupancy_board(occupancy))  # mark squares differing from expected states
            sleep(SLEEP_TIME)

    def _hw_play_move_opponent(self):
        """ Inform hardware of opponents move"""
        with self._playResult_lock:
            move = deepcopy(self._input_playResult.move) if self._input_playResult.move is not None else None

        if move is None:
            return

        with self._board_lock:
            is_capture = self._board.is_capture(move)

        while not self._game_is_over():
            occupancy = self._hwi.get_occupancy()
            if is_capture:  # Check if captured piece has been removed
                if not _get_square_from_matrix(occupancy, move.to_square):
                    is_capture = False
            else:
                if (not _get_square_from_matrix(occupancy, move.from_square)) \
                        and _get_square_from_matrix(occupancy, move.to_square):
                    # If move has been completed update board and clear input field
                    with self._board_lock:
                        self._board.push(move)
                    with self._playResult_lock:
                        self._input_playResult = None
                    temp = self._diff_occupancy_board(occupancy)
                    self._hwi.mark_squares(temp)
                    return

            # If move has not been made on hw
            diff = self._diff_occupancy_board(occupancy)  # find diff
            diff[chess.square_file(move.from_square)][chess.square_rank(move.from_square)] = True  # And mark new move
            diff[chess.square_file(move.to_square)][chess.square_rank(move.to_square)] = True

            self._hwi.mark_squares(diff)  # Send marked squares to hardware
            sleep(SLEEP_TIME)

    def _diff_occupancy_board(self, occupancy: List[List[bool]]) -> List[List[bool]]:
        """ Returns 8x8 matrix where result[i][j] == True indicates that square[i][j] is not in the expected state """
        diff = [[False] * 8 for _ in range(8)]  # matrix with squares to mark
        # Detect if hardware is in board position
        for file in range(8):
            for rank in range(8):
                square = chess.square(file, rank)
                with self._board_lock:
                    if occupancy[file][rank] == (self._board.piece_at(square) is None):
                        # If no piece at occupied square or piece at empty square mark diff as True
                        diff[file][rank] = True
        return diff

    def _game_is_over(self) -> bool:
        """ Checks if the game has ended"""
        result = False
        with self._board_lock:
            if self._board.is_checkmate():
                result = True
        with self._playResult_lock:
            if self._input_playResult is not None:
                if self._input_playResult.resigned:
                    result = True
        with self._flag_lock:
            if self._stop_flag:
                result = True
        return result
