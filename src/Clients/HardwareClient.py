import threading
from threading import Lock
from Clients import PlayerClientInterface
import chess
from chess import engine
from Hardware import HardwareImplementation, HardwareInterface
from time import sleep
from typing import List, Optional
from copy import deepcopy

SLEEP_TIME = 0.5  # Time to sleep after every scan in seconds


def _get_occupancy_square_from_matrix(occupancy_matrix: List[List[bool]], square: chess.Square) -> bool:
    """ Check if square is occupied in occupancy matrix

    A chess square (ie b3) has a file (b = file 1) and a rank (3 = file 2) now if square b3 is occupied
    then in the occupancy matrix occupancy_matrix[1][2] = TRUE. In this case this method will return TRUE
    otherwise the method will return false
    :param occupancy_matrix: 8x8 matrix of booleans implemented as a 2d list.
    :param square: The square to be checked
    :return: TRUE iff square is occupied
    """
    return occupancy_matrix[chess.square_file(square)][chess.square_rank(square)]


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
    _flag_lock: Lock = Lock()  # Required to change flag

    def __init__(self, color: chess.Color) -> None:
        """ Creates client and starts thread to control hardware chessboard
        :param color: Weather the client is black or white
        """
        self._color = color
        self._hw_thread = threading.Thread(target=self._hw_control, name="Hardware thread")
        self._hw_thread.start()

    def __del__(self):
        """" Terminates hardware thread before deleting shared resources """
        with self._flag_lock:
            self._stop_flag = True
        self._hw_thread.join()

    def get_move(self) -> chess.engine.PlayResult:
        """ Returns next move from client
        :returns: next move played by the client in the normal engine output format
        """
        while True:
            with self._playResult_lock:
               res = self._output_playResult
            if res is not None:
                self._output_playResult = None
                return res
            else:
                sleep(SLEEP_TIME)

    def set_move(self, move: chess.engine.PlayResult):
        """ Report new move to client
        :param move: reports move of opponent to client using normal engine output format
        """
        with self._playResult_lock:
            self._input_playResult = deepcopy(move)

    def _hw_control(self):
        """ Controls the hardware and maintains the hardware state

        The main body of the hardware thread. The hardware thread can be in 3 states. The hardware loops
        trough these 3 states until the game is over.
        1.  Detect move player: In this case it is the clients turn to move. The hw_thread tries to
            detect a valid move from the player based on the current occupancy. Next to this the hw_thread
            will highlight any unexpected changes
        2.  Wait move opponent: In this state the client is waiting until the set_move method is called.
            The hw_thread will highlight unexpected changes.
        3.  Play move opponent. The client waits until the opponents move has been played on the board. The
            client highlights the opponents move and any unexpected changes.
        """
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
                self._hw_detect_move_player()
            elif case == 1:
                self._hw_wait_move_opponent()
            elif case == 2:
                self._hw_play_move_opponent()
            else:
                raise Exception("internal error")

    def _hw_detect_move_player(self):
        """ Detect move from player

        We compare the expected occupancy with the actual occupancy. If two squares are different then
        we set the square where the clients piece used to be as the from square and the other square as the too
        square. Using this we create a candidate move (from_square, to_square). If this is a legal move then we
        will place this move in the output field. Note that the chess library will detect any other side effects
        from the move like captures, promotions and en passant. The internal board will be updated correctly
        and the diff will be marked on the board.
        """
        while not self._game_is_over():
            occupancy = self._hwi.get_occupancy()
            diff = self._diff_occupancy_board(occupancy)
            self._hwi.mark_squares(diff)

            # Detect all changed squares
            squares = []
            for file in range(8):
                for rank in range(8):
                    if diff[file][rank]:
                        squares.append(chess.square(file, rank))

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
                    with self._board_lock:
                        self._board.push(move)
                    with self._playResult_lock:
                        self._output_playResult = engine.PlayResult(move, None)
                    return
            sleep(SLEEP_TIME)

    def _hw_wait_move_opponent(self):
        """ Wait for opponent move only mark changes from expected state """
        while not self._game_is_over():
            with self._playResult_lock:
                if self._input_playResult is not None:
                    return
            occupancy = self._hwi.get_occupancy()
            self._hwi.mark_squares(self._diff_occupancy_board(occupancy))  # mark squares differing from expected states
            sleep(SLEEP_TIME)

    def _hw_play_move_opponent(self):
        """ Inform hardware of opponents move by marking from and to square + any other changes """
        with self._playResult_lock:
            # Deepcopy made to ensure thread safety
            move = deepcopy(self._input_playResult.move) if self._input_playResult.move is not None else None

        if move is None:
            return

        with self._board_lock:
            is_capture = self._board.is_capture(move)

        while not self._game_is_over():
            occupancy = self._hwi.get_occupancy()
            if is_capture:  # Check if captured piece has been removed
                if not _get_occupancy_square_from_matrix(occupancy, move.to_square):
                    is_capture = False
            else:
                if (not _get_occupancy_square_from_matrix(occupancy, move.from_square)) \
                        and _get_occupancy_square_from_matrix(occupancy, move.to_square):
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
        """ Checks if the game has ended

        Conditions checked
        1.  Checkmate
        2.  Opponent resignation
        3.  Stop flag raised
        """
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
