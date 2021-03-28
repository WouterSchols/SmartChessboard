from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, call
import mock as mock
from Clients import HardwareClient
import chess
from chess import engine


@mock.patch('Clients.HardwareClient.HardwareClient._hwi')
class TestHardwareClient(TestCase):

    hc: HardwareClient.HardwareClient

    def setUp(self):
        HardwareClient.HardwareClient.SLEEP_TIME = 0
        with patch('threading.Thread'):  # Prevent thread startup
            self.hc = HardwareClient.HardwareClient(chess.WHITE)

    def tearDown(self):
        self.hc._board.reset()  # Needed to prevent rare bug in chess.board library somehow
        self.hc.__del__()

    def test_get_move(self, _):
        """ Test get_move method"""
        play_result = engine.PlayResult(chess.Move(chess.square(0, 1), chess.square(0, 3)), None)
        self.hc._output_playResult = play_result
        self.assertEqual(self.hc.get_move(), play_result, "Output move not returned")
        self.assertEqual(self.hc._output_playResult, None, "Internal output field not cleared")

    def test_set_move(self, _):
        """ Test set_move method """
        input_pr = engine.PlayResult(chess.Move(chess.square(0, 1), chess.square(0, 3)), None)
        self.hc.set_move(input_pr)
        internal_pr = self.hc._input_playResult
        self.assertNotEqual(internal_pr, input_pr, "HC should not reuse input object for threadsafety")

        #  Move overrides __eq__ check if move is a new object
        input_pr.move.to_square = chess.square(0, 2)
        self.assertNotEqual(internal_pr.move, input_pr.move, "HC should not reuse input object for threadsafety")

    def test__hw_control_case_1(self, _):
        """ Test _hw_control player move"""
        self.hc._board.turn = chess.WHITE
        self.hc.color = chess.WHITE
        with patch.object(HardwareClient.HardwareClient, '_game_is_over') as game_over_mock:
            game_over_mock.side_effect = [False, True]
            with patch.object(HardwareClient.HardwareClient, '_hw_detect_player_move') as target_mock:
                self.hc._hw_control()
                self.assertTrue(target_mock.called, "Expected method was not called")

    def test__hw_control_case_2(self, _):
        """ Test _hw_control wait for opponent move"""
        self.hc._board.turn = chess.BLACK
        self.hc.color = chess.WHITE
        self.hc._input_playResult = None
        with patch.object(HardwareClient.HardwareClient, '_game_is_over') as game_over_mock:
            game_over_mock.side_effect = [False, True]
            with patch.object(HardwareClient.HardwareClient, '_hw_wait_move_opponent') as target_mock:
                self.hc._hw_control()
                self.assertTrue(target_mock.called, "Expected method was not called")

    def test__hw_control_case_3(self, _):
        """ Test _hw_control wait for opponent move to be played on hardware"""
        self.hc._board.turn = chess.BLACK
        self.hc.color = chess.WHITE
        self.hc._input_playResult = engine.PlayResult(chess.Move(chess.square(0, 1), chess.square(0, 3)), None)
        with patch.object(HardwareClient.HardwareClient, '_game_is_over') as game_over_mock:
            game_over_mock.side_effect = [False, True]
            with patch.object(HardwareClient.HardwareClient, '_hw_play_move_opponent') as target_mock:
                self.hc._hw_control()
                self.assertTrue(target_mock.called, "Expected method was not called")

    def test__hw_detect_player_move_normal(self, hwi_mock):
        """ Test detect normal move """
        # Configure occupancy
        set_occupancy(hwi_mock, self.hc._board)
        hwi_mock.get_occupancy.return_value[0][1] = False
        hwi_mock.get_occupancy.return_value[0][3] = True

        # Play move itr 1, itr 2 terminate
        with patch.object(HardwareClient.HardwareClient, '_game_is_over') as game_over_mock:
            game_over_mock.side_effect = [False,  True]
            self.hc._hw_detect_player_move()

        self.assertIsNotNone(self.hc._output_playResult, "Output move has not been processed")
        self.assertEqual(self.hc._output_playResult.move, chess.Move(chess.square(0, 1), chess.square(0, 3)),
                         "Detected move was not a4")

    def test__hw_detect_player_move_capture(self, hwi_mock):
        """ Test detect normal capture """
        # Set up board
        self.hc._board.push(chess.Move(chess.square(1, 1), chess.square(1, 3)))  # b4
        self.hc._board.push(chess.Move(chess.square(0, 6), chess.square(0, 4)))  # a5

        # Configure occupancy
        set_occupancy(hwi_mock, self.hc._board)
        hwi_mock.get_occupancy.return_value[1][3] = False
        hwi_mock.get_occupancy.return_value[0][4] = False

        # Play move itr 1, itr 2 terminate
        with patch.object(HardwareClient.HardwareClient, '_game_is_over') as game_over_mock:
            game_over_mock.side_effect = [False,  True]
            self.hc._hw_detect_player_move()

        self.assertIsNotNone(self.hc._output_playResult, "Output move has not been processed")
        self.assertEqual(self.hc._output_playResult.move, chess.Move(chess.square(1, 3), chess.square(0, 4)),
                         "Detected move was not a5")

    def test__hw_detect_player_move_promote(self, hwi_mock):
        """ Test detect promotion """
        # Set up board
        self.hc._board.set_fen("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")  # Lone pawn a7
        # Configure occupancy
        set_occupancy(hwi_mock, self.hc._board)
        hwi_mock.get_occupancy.return_value[0][6] = False
        hwi_mock.get_occupancy.return_value[0][7] = True

        # Play move itr 1, itr 2 terminate
        with patch.object(HardwareClient.HardwareClient, '_game_is_over') as game_over_mock:
            game_over_mock.side_effect = [False,  True]
            self.hc._hw_detect_player_move()

        self.assertIsNotNone(self.hc._output_playResult, "Output move has not been processed")
        self.assertEqual(self.hc._output_playResult.move, chess.Move(chess.square(0, 6),
                                                                     chess.square(0, 7), chess.QUEEN),
                         "Detected move was not a8Q")

    def test__hw_detect_player_move_reject_opponent(self, hwi_mock):
        """ Test that opponent moves are rejected """
        # Configure occupancy
        set_occupancy(hwi_mock, self.hc._board)
        hwi_mock.get_occupancy.return_value[0][6] = False
        hwi_mock.get_occupancy.return_value[0][4] = True

        # Play move itr 1, itr 2 terminate
        with patch.object(HardwareClient.HardwareClient, '_game_is_over') as game_over_mock:
            game_over_mock.side_effect = [False, True]
            self.hc._hw_detect_player_move()

        self.assertIsNone(self.hc._output_playResult, "Opponent move detected as player move")

    def test__hw_detect_player_move_reject_incomplete(self, hwi_mock):
        """ Test that incomplete moves are not accepted """
        # Configure occupancy
        set_occupancy(hwi_mock, self.hc._board)
        hwi_mock.get_occupancy.return_value[0][1] = False

        # Play move itr 1, itr 2 terminate
        with patch.object(HardwareClient.HardwareClient, '_game_is_over') as game_over_mock:
            game_over_mock.side_effect = [False, True]
            self.hc._hw_detect_player_move()

        self.assertIsNone(self.hc._output_playResult, "Incorrectly detected move")

    def test__hw_detect_player_move_reject_illegal(self, hwi_mock):
        """ Test that illegal moves are not accepted """
        # Set up board
        self.hc._board.set_fen("3kr3/8/8/8/8/8/P7/4K3 w - - 0 1")  # Pawn a2 but king in check
        # Configure occupancy
        set_occupancy(hwi_mock, self.hc._board)
        hwi_mock.get_occupancy.return_value[0][1] = False
        hwi_mock.get_occupancy.return_value[0][3] = True

        # Play move itr 1, itr 2 terminate
        with patch.object(HardwareClient.HardwareClient, '_game_is_over') as game_over_mock:
            game_over_mock.side_effect = [False, True]
            self.hc._hw_detect_player_move()

        self.assertIsNone(self.hc._output_playResult, "Illegal move accepted")

    def test__hw_detect_player_move_reject_corrupted(self, hwi_mock):
        """ Test that corrupted moves are not accepted """
        # Configure occupancy
        set_occupancy(hwi_mock, self.hc._board)
        hwi_mock.get_occupancy.return_value[0][1] = False
        hwi_mock.get_occupancy.return_value[0][3] = True
        hwi_mock.get_occupancy.return_value[0][4] = True

        # Play move itr 1, itr 2 terminate
        with patch.object(HardwareClient.HardwareClient, '_game_is_over') as game_over_mock:
            game_over_mock.side_effect = [False, True]
            self.hc._hw_detect_player_move()

        self.assertIsNone(self.hc._output_playResult, "Incorrectly detected move")

    def test__hw_wait_move_opponent(self, _):
        """ Test if method terminates once input is given """
        self.hc._input_playResult = engine.PlayResult(chess.Move(chess.square(0, 1), chess.square(0, 3)), None)
        self.hc._hw_wait_move_opponent()

    def test__hw_play_move_opponent_move_None(self, _):
        """ Test if method does not crash when input is not a move """
        self.hc._input_playResult = engine.PlayResult(None, None, resigned=True)
        self.hc._hw_play_move_opponent()

    def test__hw_play_move_opponent_move_normal(self, hwi_mock):
        """ Test normal input move """
        self.hc._input_playResult = engine.PlayResult(
            chess.Move(chess.square(0, 1), chess.square(0, 3)), None)  # New move pawn a4

        # Configure occupancy for first and second call
        set_occupancy(hwi_mock, self.hc._board)
        occ1 = deepcopy(hwi_mock.get_occupancy.return_value)
        occ2 = deepcopy(hwi_mock.get_occupancy.return_value)
        occ2[0][1] = False
        occ2[0][3] = True
        hwi_mock.get_occupancy.side_effect = [occ1, occ2]

        # Play move itr 1 no move, itr 2 move made, itr 3 terminate
        with patch.object(HardwareClient.HardwareClient, '_game_is_over') as game_over_mock:
            game_over_mock.side_effect = [False, False, True]
            self.hc._hw_play_move_opponent()

        self.assertIsNone(self.hc._input_playResult, "Input move has not been processed correctly")

        # Check that in first iteration a2 and a4 are marked and next iteration no squares are marked
        marking2 = [[False]*8 for _ in range(8)]
        marking1 = deepcopy(marking2)
        marking1[0][1] = True
        marking1[0][3] = True
        hwi_mock.mark_squares.assert_has_calls([call(marking1), call(marking2)], "Incorrect squares have been marked")

    def test__hw_play_move_opponent_move_capture(self, hwi_mock):
        """ Test capture input move """
        self.hc._board.push(chess.Move(chess.square(1, 1), chess.square(1, 3)))  # b4
        self.hc._board.push(chess.Move(chess.square(0, 6), chess.square(0, 4)))  # a5
        self.hc._input_playResult = engine.PlayResult(
            chess.Move(chess.square(1, 3), chess.square(0, 4)), None)  # New move capture a5

        # Configure occupancy for first, second and third call
        set_occupancy(hwi_mock, self.hc._board)
        occ1 = deepcopy(hwi_mock.get_occupancy.return_value)
        occ2 = deepcopy(hwi_mock.get_occupancy.return_value)
        occ3 = deepcopy(hwi_mock.get_occupancy.return_value)
        occ2[1][3] = False
        occ2[0][4] = False
        occ3[1][3] = False
        occ3[0][4] = True
        hwi_mock.get_occupancy.side_effect = [occ1, occ2, occ3]

        # Itr 1 no move, itr 2 remove captured piece, itr3 add new piece, itr 4 terminate
        with patch.object(HardwareClient.HardwareClient, '_game_is_over') as game_over_mock:
            game_over_mock.side_effect = [False, False, False, True]
            self.hc._hw_play_move_opponent()

        self.assertIsNone(self.hc._input_playResult, "Input move has not been processed correctly")

        # Check that in first two iterations b4 and a5 are marked and next iteration no squares are marked
        marking3 = [[False]*8 for _ in range(8)]
        marking1 = deepcopy(marking3)
        marking1[1][3] = True
        marking1[0][4] = True
        marking2 = deepcopy(marking1)
        hwi_mock.mark_squares.assert_has_calls(
            [call(marking1), call(marking2), call(marking3)], "Incorrect squares have been marked")

    def test__hw_play_move_opponent_move_castle(self, hwi_mock):
        """ Test castle input move """
        self.hc._board.set_fen("4k3/8/8/8/8/8/8/4K2R w K - 0 1")
        self.hc._input_playResult = engine.PlayResult(
            chess.Move(chess.square(4, 0), chess.square(6, 0)), None)  # New move O-O

        # Configure occupancy for first, second and third call
        set_occupancy(hwi_mock, self.hc._board)
        occ1 = deepcopy(hwi_mock.get_occupancy.return_value)
        occ2 = deepcopy(hwi_mock.get_occupancy.return_value)
        occ2[4][0] = False
        occ2[6][0] = True
        hwi_mock.get_occupancy.side_effect = [occ1, occ2]

        # Itr 1 no move, itr 2 move, itr 4 terminate
        with patch.object(HardwareClient.HardwareClient, '_game_is_over') as game_over_mock:
            game_over_mock.side_effect = [False, False, True]
            self.hc._hw_play_move_opponent()

        self.assertIsNone(self.hc._input_playResult, "Input move has not been processed correctly")

        # Check that in first iteration e1 and g1 are marked and next iteration f1 and h1 are marked
        marking1 = [[False]*8 for _ in range(8)]
        marking2 = deepcopy(marking1)
        marking1[4][0] = True
        marking1[6][0] = True
        marking2[7][0] = True  # Rook move still needs to be played but king move is sufficient to finish method
        marking2[5][0] = True
        hwi_mock.mark_squares.assert_has_calls(
            [call(marking1), call(marking2)], "Incorrect squares have been marked")

    def test__hw_play_move_opponent_move_promote(self, hwi_mock):
        """ Test promotion move """
        self.hc._board.set_fen("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")  # Lone pawn a7
        self.hc._input_playResult = engine.PlayResult(
            chess.Move(chess.square(0, 6), chess.square(0, 7), chess.QUEEN), None)  # New move a8Q

        # Configure occupancy for first, second and third call
        set_occupancy(hwi_mock, self.hc._board)
        occ1 = deepcopy(hwi_mock.get_occupancy.return_value)
        occ2 = deepcopy(hwi_mock.get_occupancy.return_value)

        occ2[0][6] = False
        occ2[0][7] = True
        hwi_mock.get_occupancy.side_effect = [occ1, occ2]

        # Itr 1 no move, itr 2 promoted piece, itr 3 terminate
        with patch.object(HardwareClient.HardwareClient, '_game_is_over') as game_over_mock:
            game_over_mock.side_effect = [False, False, True]
            self.hc._hw_play_move_opponent()

        self.assertIsNone(self.hc._input_playResult, "Input move has not been processed correctly")

        # Check that in first iterations a7 and a8 are marked
        marking2 = [[False] * 8 for _ in range(8)]
        marking1 = deepcopy(marking2)
        marking1[0][6] = True
        marking1[0][7] = True
        hwi_mock.mark_squares.assert_has_calls([call(marking1), call(marking2)], "Incorrect squares have been marked")

    def test__diff_occupancy_board_same(self, hwi_mock):
        """ Assert _diff_occupancy_board does not detect a diff if occupancy has expected value """
        set_occupancy(hwi_mock, self.hc._board)
        diff = self.hc._diff_occupancy_board(hwi_mock.get_occupancy.return_value)
        self.assertEqual(diff, [[False] * 8 for _ in range(8)], "Detected difference from expected occupancy")

    def test__diff_occupancy_board_diff(self, hwi_mock):
        """ Assert _diff_occupancy_board does not detect a diff if occupancy has expected value """
        set_occupancy(hwi_mock, self.hc._board)
        self.hc._board.push(chess.Move(chess.square(0, 1), chess.square(0, 3)))  # Move pawn a4
        diff = self.hc._diff_occupancy_board(hwi_mock.get_occupancy.return_value)
        expected = [[False]*8 for _ in range(8)]
        expected[0][1] = True
        expected[0][3] = True
        self.assertEqual(diff, expected, "Incorrectly detected change in expected occupancy")

    @mock.patch('Clients.HardwareClient.HardwareClient._board')
    def test__game_is_over(self, board_mock, _):
        """ Simple unit Test to detect if game is over """
        board_mock.is_checkmate.return_value = False
        self.assertFalse(self.hc._game_is_over(), "Incorrectly detected game over")

        self.hc._stop_flag = True
        self.assertTrue(self.hc._game_is_over(), "Setting stop flag ignored")

        self.hc._stop_flag = False
        self.hc._input_playResult = chess.engine.PlayResult(None, None, resigned=True)
        self.assertTrue(self.hc._game_is_over(), "Resign ignored")

        self.hc._input_playResult = None
        board_mock.is_checkmate.return_value = True
        self.assertTrue(self.hc._game_is_over(), "Checkmate ignored")


def set_occupancy(hwi_mock, board_mock):
    """ Sets the return value of hwi.get_occupancy to the expected state from board"""
    occupancy = [[False]*8 for _ in range(8)]
    for file in range(8):
        for rank in range(8):
            square = chess.square(file, rank)
            occupancy[file][rank] = board_mock.piece_at(square) is not None
    hwi_mock.get_occupancy.return_value = occupancy
