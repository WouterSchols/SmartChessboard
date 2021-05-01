from typing import Optional, Tuple
import chess
import time
from datetime import timedelta
from chess import engine
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
from Clients import ClientInterface


class ChessDotComClient(ClientInterface.ClientInterface):
    """ Defines interface to play on chess.com """

    _driver: webdriver
    color: chess.Color

    def __init__(self, headless: bool = False, path_userdata: str = None):
        """ Starts the chess.com client.

        Using the chess.com client requires that chromedriver to be installed. Starting the client will open a new
        chromedriver window. No version of chrome should be running if the path_userdata is set. The game starts once
        the start method is called
        :param headless: Needs to be set to false if the device running the code is headless
        :param path_userdata: Optional path to the chrome user date, allows chess.com to remember login
        """
        options = webdriver.ChromeOptions()
        if path_userdata is not None:
            options.add_argument("user-data-dir=" + path_userdata)
        if headless:
            options.headless = True

        self._driver = webdriver.Chrome(options=options)
        self._driver.get("https://www.chess.com")
        # Check if game is ready and set color
        super().__init__(self.start_new_game())
        print("game started as " + ("black" if self.color else "white"))

    def __del__(self):
        """" Terminates engine """
        self._driver.quit()

    def get_move(self) -> chess.engine.PlayResult:
        """ Returns next move from client
        :returns: next move played by the client in the normal engine output format
        """
        while True:

            try:
                # Find highlighted squares
                res = self._driver.find_elements_by_xpath("//div[starts-with(@data-test-element,'highlight')]")
                if len(res) >= 2:
                    # Two highlighted square indicate a move, first hit usually from square second to square
                    from_square_id = res[0].get_attribute("class")[-2:]  # Last two char of class name is the square
                    to_square_id = res[1].get_attribute("class")[-2:]
                    from_square = chess.square(int(from_square_id[0]) - 1, int(from_square_id[1]) - 1)
                    to_square = chess.square(int(to_square_id[0]) - 1, int(to_square_id[1]) - 1)

                    # Set from and to square
                    if self._board.piece_at(from_square) is None \
                            or self._board.piece_at(from_square).color is not self.color:
                        temp = from_square
                        from_square = to_square
                        to_square = temp

                    # If new move is promotion
                    if self._board.piece_at(from_square) is not None \
                            and self._board.piece_at(from_square).piece_type is chess.PAWN \
                            and chess.square_rank(to_square) == (7 if self.color is chess.WHITE else 0):
                        # Check promotion square (it has a unique name)
                        promotion_square_id = "piece.square-{piece_file}{piece_rank}.{piece_color}".format(
                            piece_file=chess.square_file(to_square) + 1,
                            piece_rank=chess.square_rank(to_square) + 1,
                            piece_color='w' if self.color is chess.WHITE else 'b'
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
                        res = self._driver.find_elements_by_class_name(
                            "form-button-component.form-button-small.form-button-primary.draw-offer-accept")
                        draw_offer = res != []
                        return chess.engine.PlayResult(move, None, draw_offered=draw_offer)
                    else:  # Old move found
                        time.sleep(0.5)
            except StaleElementReferenceException:  # Occurs if new move is played during processing
                pass

    def set_move(self, move: engine.PlayResult):
        """ Report new move to client
        :param move: reports move of opponent to client using normal engine output format
        """
        if move.move is None:
            if move.resigned:
                resign_button = self._driver.find_elements_by_class_name("secondary-controls-icon")
                # If a bot is being played
                if len(resign_button) != 0:
                    resign_button[-1].click()
                else:
                    # Resign confirmation should be turned off
                    self._driver.find_element_by_class_name("resign-button-component.live-game-buttons-button").click()
                return
            else:
                raise Exception("Internal error empty move given as input")

        if move.draw_offered:
            draw = self._driver.find_element_by_class_name("draw-button-component.live-game-buttons-button")
            draw.click()

        piece = self._board.piece_at(move.move.from_square)
        self._board.push(move.move)
        piece_char: str = chess.piece_symbol(piece.piece_type).lower()
        piece_color = 'w' if piece.color == chess.WHITE else 'b'
        piece_elem_name = "piece.{piece_color}{piece_char}.square-{piece_file}{piece_rank}".format(
            piece_color=piece_color,
            piece_char=piece_char,
            piece_file=chess.square_file(move.move.from_square) + 1,
            piece_rank=chess.square_rank(move.move.from_square) + 1)

        # Find square with the piece to move
        piece_elem = self._driver.find_element_by_class_name(piece_elem_name)
        square_height = piece_elem.size['height']

        # Calculate relative position of to square from whites perspective
        transpose_file = chess.square_file(move.move.to_square) - chess.square_file(move.move.from_square)
        transpose_rank = chess.square_rank(move.move.to_square) - chess.square_rank(move.move.from_square)

        # Flip transpose if player if black
        transpose_file = transpose_file if self.color is chess.WHITE else -transpose_file
        transpose_rank = transpose_rank if self.color is chess.WHITE else - transpose_rank

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

    def game_is_over(self) -> bool:
        """ Checks if game is over by checking if the position is mate or the game over window is open
        :return: Returns True iff game is over
        """
        game_end_name = "section-container-component-light-mode-modal-content-component.modal-game-over" \
                        "-component.modal-game-over-rounded-grey"
        return self._driver.find_elements_by_class_name(game_end_name) != [] or self._board.is_game_over()

    def synchronize_clocks(self, clock: Optional[Tuple[timedelta, timedelta]] = None) \
            -> Optional[Tuple[timedelta, timedelta]]:
        """ Obtains time from chess.com if clock is running else returns input
        :param clock: Input clock from the other client
        :return: return clock from current client
        """

        client = self._driver.find_elements_by_xpath("//*[@id='board-layout-player-top']//div//div[3]/span")
        opponent = self._driver.find_elements_by_xpath("//*[@id='board-layout-player-bottom']//div//div[3]/span")

        if client is not [] and opponent is not []:
            client_time_str = str(client[0].text).split(":")
            client_time = timedelta(minutes=int(client_time_str[0]),
                                    seconds=int(client_time_str[1].replace(":", "")))
            opponent_time_str = str(client[0].text).split(":")
            opponent_time = timedelta(minutes=int(opponent_time_str[0]),
                                      seconds=int(opponent_time_str[1].replace(":", "")))
            return (client_time, opponent_time) if self.color else (opponent_time, client_time)
        else:
            return clock

    def start_new_game(self) -> chess.Color:
        """ Resets the client to start a new game

        This method can be used to start a new game using the same client. This prevents us from having to reload the
        chromedriver
        :return: Returns new color of client
        """
        while True:
            if self._driver.find_elements_by_class_name("resign-button-component.live-game-buttons-button") != [] or \
                    len(self._driver.find_elements_by_class_name("secondary-controls-icon")) == 4:
                break
            else:
                time.sleep(0.5)
        # Find color of client
        y_coord_w_rook = self._driver.find_element_by_class_name("piece.wr.square-11").location['y']
        y_coord_b_rook = self._driver.find_element_by_class_name("piece.br.square-18").location['y']
        color = chess.WHITE if y_coord_b_rook > y_coord_w_rook else chess.BLACK
        self._board = chess.Board()

        # configure metadata
        names = self._driver.find_elements_by_class_name(
            "user-username-component.user-username-dark.user-username-link.user-tagline-username")
        rating = self._driver.find_elements_by_class_name("user-tagline-rating")
        if not names:
            names = self._driver.find_elements_by_class_name(
                "user-username-component.user-username-lightgray.user-tagline-username")
        if len(names) == 2:
            if 0 == len(rating):
                self.metadata[("white" if color else "black") + "_name"] = names[0].text
            else:
                self.metadata[("white" if color else "black") + "_name"] = names[0].text + " " + rating[0].text
            if 1 == len(rating):
                self.metadata[("white" if not color else "black") + "_name"] = names[1].text
            else:
                self.metadata[("white" if not color else "black") + "_name"] = names[1].text + " " + rating[1].text
        return color
