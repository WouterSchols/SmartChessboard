from Clients import ClientInterface, ConsoleClient, ChessDotComClient, EngineClient
import PySimpleGUI as Sg
import chess
import time
from typing import Optional


def create_start_screen() -> Sg.Window:
    """ Creates gui for simple start screen

    :return: A window with 3 buttons to select the client to start and an exit button
    """
    screen = [[Sg.Text("Select opponent:")],
              [Sg.Button("Chess.com"), Sg.Button("Engine"), Sg.Button("Console"),
               Sg.Button("Exit")]]
    return Sg.Window("Smart chessboard", screen)


def create_engine_screen() -> Sg.Window:
    """ Creates the engine configuration screen

    :return: Screen with all configuration settings for the engine client
    """
    screen = [[Sg.Text("Configure Engine:")],
              [Sg.FileBrowse('FileBrowse'), Sg.Input()],
              [Sg.Text('Engine time per move in s'), Sg.Input(key='time', enable_events=True)],
              [Sg.Text("Player color:"), Sg.Button('White', size=(4, 1), button_color=('black', 'white'), key='color')],
              [Sg.Button("Start Game"), Sg.Cancel()]]
    return Sg.Window("Smart chessboard", screen)


def play_console_screen() -> Sg.Window:
    """ Creates the console client configuration screen

    :return: Screen with all configuration settings for the console client
    """
    screen = [[Sg.Text("Player color:"), Sg.Button('White', size=(4, 1), button_color=('black', 'white'), key='color')],
              [Sg.Button("Start Game"), Sg.Cancel()]]
    return Sg.Window("Smart chessboard", screen)


def get_opponent_from_gui() -> Optional[ClientInterface.ClientInterface]:
    """ Main GUI method which returns the client selected as opponent

    :return: The client to use as component or None if the GUI is closed
    """
    window = create_start_screen()
    while True:
        event, values = window.read()
        if event == Sg.WIN_CLOSED or event == "Exit":
            window.close()
            return None
        if event == "Chess.com":
            window.close()
            return set_up_game_chessdotcom()
        if event == "Engine":
            window.close()
            return set_up_game_engine()
        if event == "Console":
            window.close()
            return set_up_game_console()
        time.sleep(0.5)


def set_up_game_chessdotcom() -> ClientInterface.ClientInterface:
    """ Returns the chess.com client

    :return: A chess.com client instance
    """
    return ChessDotComClient.ChessDotComClient()  # Constructor opens chrome and blocks until game is started


def set_up_game_engine() -> Optional[ClientInterface.ClientInterface]:
    """" Opens GUI to configure the engine client

    :return: An instance of the engine client with the configured settings or None if the window is closed
    """
    window = create_engine_screen()
    color = chess.WHITE
    move_time = 0.1
    while True:
        event, values = window.read()
        if event == Sg.WIN_CLOSED:
            window.close()
            return None
        if event == "Cancel":
            return get_opponent_from_gui()
        if event == 'time' and values['time'] and values['time'][-1] not in '0123456789.-':
            move_time = float(values['time'])
        if event == "color":
            color = not color
            window.Element('color').Update(('Black', 'White')[color],
                                           button_color=((('white', 'black'), ('black', 'white'))[color]))
        if event == "Start Game":
            window.close()
            try:
                return EngineClient.EngineClient(not color, values['FileBrowse'], move_time)  # not opponent.color
            except OSError:
                display_error("Could not start Engine")
                return set_up_game_engine()


def display_error(error: str):
    """ Displays a simple error message in a new window

    :param error: The message to display
    """
    screen = [[Sg.Text(error)],
              [Sg.Button("OK")]]
    window = Sg.Window("Smart chessboard", screen)
    while True:
        event, values = window.read()
        if event == Sg.WIN_CLOSED or event == "OK":
            return


def set_up_game_console() -> Optional[ClientInterface.ClientInterface]:
    """" Opens GUI to configure the console client

    :return: An instance of the console client with the configured settings or None if the window is closed
    """
    window = play_console_screen()
    color = chess.BLACK
    while True:
        event, values = window.read()
        if event == Sg.WIN_CLOSED:
            window.close()
            return None
        if event == "Cancel":
            return get_opponent_from_gui()
        if event == "color":
            color = not color
            window.Element('color').Update(('Black', 'White')[color],
                                           button_color=((('white', 'black'), ('black', 'white'))[color]))
        if event == "Start Game":
            window.close()
            return ConsoleClient.ConsoleClient(color)  # not opponent.color
