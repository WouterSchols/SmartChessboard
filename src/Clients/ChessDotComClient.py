import chess
import time
from chess import engine
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
from Clients import PlayerClientInterface

class ChessDotComClient(PlayerClientInterface.PlayerClientInterface):
    """ Defines interface to play on chess.com """

    # _board: chess.Board = chess.Board()
    _driver: webdriver
    _board: chess.Board = chess.Board()
    _color: chess.Color

    def __init__(self, color: chess.Color):
        """ Creates a chromium driver
        :param color: The color being played by the chess client
        """
        self._color = color
        options = webdriver.ChromeOptions()
        #options.add_argument("user-data-dir=c:/Users/woute/AppData/Local/Google/Chrome/User Data/")
        self._driver = webdriver.Chrome(options=options)
        self._driver.get("https://www.chess.com/play/computer")
        input("Board is ready")


    def __del__(self):
        """" Terminates engine """
        self._driver.close()

    def get_move(self) -> chess.engine.PlayResult:
        """ Returns next move from client
        :returns: next move played by the client in the normal engine output format
        """
        while True:
            # Find highlighted squares
            try:
                # res is filled with all highlighted squares
                res = self._driver.find_elements_by_xpath("//div[starts-with(@data-test-element,'highlight')]")
                if len(res) >= 2:
                    # Two highlighted square indicate a move, first hit usually from square second to square
                    from_square_id = res[0].get_attribute("class")[-2:] # Last two char of class name is the square
                    to_square_id = res[1].get_attribute("class")[-2:]
                    from_square = chess.square(int(from_square_id[0]) - 1, int(from_square_id[1]) - 1)
                    to_square = chess.square(int(to_square_id[0]) - 1, int(to_square_id[1]) - 1)

                    # Set from and to square
                    if self._board.piece_at(from_square) is None \
                        or self._board.piece_at(from_square).color is not self._color:
                        temp = from_square
                        from_square = to_square
                        to_square = temp

                    # If new move is promotion
                    if self._board.piece_at(from_square) is not None \
                            and self._board.piece_at(from_square).piece_type is chess.PAWN \
                            and chess.square_rank(to_square) == (7 if self._color is chess.WHITE else 0):
                        # Check promotion square (it has a unique name)
                        promotion_square_id = "piece.square-{piece_file}{piece_rank}.{piece_color}".format(
                            piece_file = chess.square_file(to_square) + 1,
                            piece_rank = chess.square_rank(to_square) + 1,
                            piece_color= 'w' if self._color is chess.WHITE else 'b'
                        )
                        piece: chess.Piece
                        if self._driver.find_elements_by_id(promotion_square_id + 'q') is not []:
                            piece = chess.QUEEN  # if promotion piece square contains queen
                        elif self._driver.find_elements_by_id(promotion_square_id + 'r') is not []:
                            piece = chess.ROOK
                        elif self._driver.find_elements_by_id(promotion_square_id + 'n') is not []:
                            piece = chess.KNIGHT
                        elif self._driver.find_elements_by_id(promotion_square_id + 'b') is not []:
                            piece = chess.BISHOP
                        else:
                            raise Exception("Promotion piece detection failed")

                        # set move with promotion field
                        move = chess.Move(from_square, to_square, promotion=piece)
                    else:
                        # If no promotion just set new move
                        move = chess.Move(from_square, to_square)

                    if move in self._board.legal_moves:
                        # if the move is legal
                        self._board.push(move)
                        return chess.engine.PlayResult(move, None)
                    else: # Old move found
                        time.sleep(0.5)
            except StaleElementReferenceException:  # Occurs if new move is played during processing
                pass

    def set_move(self, move: engine.PlayResult):
        """ Report new move to client
        :param move: reports move of opponent to client using normal engine output format
        """
        if move.move is None:
            return

        piece = self._board.piece_at(move.move.from_square)
        self._board.push(move.move)
        piece_char: str = chess.piece_symbol(piece.piece_type).lower()
        piece_color = 'w' if piece.color == chess.WHITE else 'b'
        piece_elem_name = "piece.{piece_color}{piece_char}.square-{piece_file}{piece_rank}".format(
            piece_color=piece_color,
            piece_char = piece_char,
            piece_file = chess.square_file(move.move.from_square) + 1,
            piece_rank = chess.square_rank(move.move.from_square) + 1)

        # Find square with the piece to move
        piece_elem = self._driver.find_element_by_class_name(piece_elem_name)
        square_height = piece_elem.size['height']

        # Calculate relative position of to square from whites perspective
        transpose_file = chess.square_file(move.move.to_square) - chess.square_file(move.move.from_square)
        transpose_rank = chess.square_rank(move.move.to_square) - chess.square_rank(move.move.from_square)

        # Flip transpose if player if black
        transpose_file = transpose_file if self._color is chess.WHITE else -transpose_file
        transpose_rank = transpose_rank if self._color is chess.WHITE else - transpose_rank

        # Drag piece with transposition
        act = ActionChains(self._driver)
        act.drag_and_drop_by_offset(piece_elem,
                                        - transpose_file * square_height,
                                        transpose_rank * square_height).perform()

        if move.move.promotion is not None:
            time.sleep(0.1)
            piece_char: str = chess.piece_symbol(move.move.promotion).lower()
            piece_elem_name = "promotion-piece.{piece_color}{piece_char}".format(
                piece_color=piece_color,
                piece_char=piece_char)
            piece_elem = self._driver.find_element_by_class_name(piece_elem_name)
            piece_elem.click()
