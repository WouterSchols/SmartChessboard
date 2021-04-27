import threading
from threading import Lock
from Clients import ClientInterface
import chess
from chess import engine
from Hardware import HardwareImplementation, HardwareInterface
from time import sleep
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from copy import deepcopy

SLEEP_TIME = 0.5  # Time to sleep after every scan in seconds


class HardwareClient(ClientInterface.ClientInterface):
    """ Interface to Hardware chessboard"""

    # Board state
    _board_lock: Lock  # Required to access _board

    # Input output variables
    _input_playResult: Optional[chess.engine.PlayResult]
    _output_playResult: Optional[chess.engine.PlayResult]
    _playResult_lock: Lock  # Required to access input or output

    # Time display
    _white_time: Optional[timedelta]
    _black_time: Optional[timedelta]
    _last_move_made: datetime
    _time_lock: Lock  # Required to display the time

    # HardwareInterface thread variables
    _hw_thread: threading.Thread
    _hwi: HardwareInterface.HardwareInterface
    _stop_flag: bool
    _flag_lock: Lock  # Required to change flag

    def __init__(self, color: chess.Color):
        """ Creates client and starts thread to control hardware chessboard
        :param color: Weather the client is black or white
        """
        super().__init__(color)
        self._board_lock = Lock()  # Required to access _board

        # Input output variables
        self._input_playResult = None
        self._output_playResult = None
        self._playResult_lock = Lock()
        self._white_time = None
        self._black_time = None
        self._last_move_made = datetime.now()
        self._time_lock = Lock()

        # Client to the HardwareInterface
        self._hw_thread = threading.Thread(target=self._hw_control, name="Hardware thread")
        self._hwi: HardwareInterface = HardwareImplementation.HardwareImplementation()
        self._stop_flag = False
        self._flag_lock = Lock()

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
        with self._time_lock:
            self._last_move_made = datetime.now()
        with self._playResult_lock:
            self._input_playResult = deepcopy(move)

    def game_is_over(self) -> bool:
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

    def synchronize_clocks(self, clock: Optional[Tuple[timedelta, timedelta]] = None) \
            -> Optional[Tuple[timedelta, timedelta]]:
        """ Synchronize clocks between two clients
        :param clock: Input clock from the other client (white time, black time)
        :return: return clock from current client (white time, black time) if available
        """
        with self._time_lock:
            if clock is not None:
                self._white_time = clock[0]
                self._black_time = clock[1]
            if self._white_time is None or self._black_time is None:
                return None
            else:
                return deepcopy(self._white_time), deepcopy(self._black_time)

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

        if self.color == chess.WHITE:
            self._hwi.display("White")
        else:
            self._hwi.display("Black")

        while not self.game_is_over():
            case = -1
            with self._board_lock:
                if self._board.turn == self.color:
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
        draw_offer = False
        while not self.game_is_over():
            occupancy = self._hwi.get_occupancy()
            diff = self._diff_occupancy_board(occupancy)
            self._hwi.mark_squares(diff)

            offers = self._hwi.game_end_offers()
            if offers is HardwareInterface.Offer.RESIGN:
                self._resigned = True
                return engine.PlayResult(None, None, resigned=True)
            if offers is HardwareInterface.Offer.DRAW:
                draw_offer = True

            # Detect all changed squares
            squares = []
            for file in range(8):
                for rank in range(8):
                    if diff[file][rank]:
                        squares.append(chess.square(file, rank))

            if len(squares) == 2:  # Try to convert changed squares to legal move
                with self._board_lock:  # Promotion not implemented
                    if self._board.piece_at(squares[0]) is not None and \
                            self._board.piece_at(squares[0]).color == self.color:
                        move = chess.Move(squares[0], squares[1])
                    elif self._board.piece_at(squares[1]) is not None and \
                            self._board.piece_at(squares[1]).color == self.color:
                        move = chess.Move(squares[1], squares[0])
                    else:
                        continue
                    if self._board.piece_at(move.from_square).piece_type == chess.PAWN and \
                            ((self.color == chess.WHITE and chess.square_rank(move.to_square) == 7) or
                             (self.color == chess.BLACK and chess.square_rank(move.to_square) == 0)):
                        move.promotion = chess.QUEEN
                    move_is_legal = move in self._board.legal_moves  # save result to not use two locks
                    if move_is_legal:
                        move.promotion = self._hwi.promotion_piece()

                if move_is_legal:
                    with self._board_lock:
                        self._board.push(move)
                    with self._playResult_lock:
                        self._output_playResult = engine.PlayResult(move, None, draw_offered=draw_offer)
                    return
            self._update_display()
            sleep(SLEEP_TIME)

    def _hw_wait_move_opponent(self):
        """ Wait for opponent move only mark changes from expected state """
        while not self.game_is_over():
            with self._playResult_lock:
                if self._input_playResult is not None:
                    return
            occupancy = self._hwi.get_occupancy()
            self._hwi.mark_squares(self._diff_occupancy_board(occupancy))  # mark squares differing from expected states
            self._update_display()
            sleep(SLEEP_TIME)

    def _hw_play_move_opponent(self):
        """ Inform hardware of opponents move by marking from and to square + any other changes """
        with self._playResult_lock:
            # Deepcopy made to ensure thread safety
            move = deepcopy(self._input_playResult.move) if self._input_playResult.move is not None else None
            draw_offered = self._input_playResult.draw_offered

        if move is None:
            return

        with self._board_lock:
            is_capture = self._board.is_capture(move)

        while not self.game_is_over():
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
            if draw_offered:
                self._hwi.display("Draw offered")
            else:
                self._update_display()
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

    def _update_display(self):
        """ Writes information to the display
            In the first four moves the name of the players will be displayed from the metadata after that the clock
            will be displayed
        """
        with self._time_lock:
            time_set = self._white_time is not None and self._black_time is not None
        meta_data_set = "white_name" in self.metadata and "black_name" in self.metadata
        with self._board_lock:
            early_game = len(self._board.move_stack) <= 4
            color = self._board.turn
        if meta_data_set and (early_game or not time_set):
            self._hwi.display(self.metadata["white_name"] + "\n" + self.metadata["black_name"])
        elif time_set:
            with self._time_lock:
                if color:
                    self._white_time = self._last_move_made + self._white_time - datetime.now()
                else:
                    self._black_time = self._last_move_made + self._black_time - datetime.now()
                self._last_move_made = datetime.now()

                str_white = "White {minutes}:{seconds:02d}".format(
                    minutes=int(self._white_time.seconds / 60),
                    seconds=self._white_time.seconds % 60)
                str_black = "Black {minutes}:{seconds:02d}".format(
                    minutes=int(self._black_time.seconds / 60),
                    seconds=self._black_time.seconds % 60)
                self._hwi.display(str_white + "\n" + str_black)


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
