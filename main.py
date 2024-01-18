import tkinter as tk
from tkinter import ttk
import numpy as np
import random as rnd
from threading import Thread
from queue import Queue


disk_color = ['white', 'red', 'orange']
disks = list()

player_type = ['human']
for i in range(42):
    player_type.append('AI: alpha-beta level '+str(i+1))

def alpha_beta_decision(board, turn, ai_level, queue, max_player):
    depth = ai_level
    alpha = float('-inf')
    beta = float('inf')

    column, _ = minimax(board, depth, alpha, beta, max_player, max_player)
    queue.put(column)


memoization = {}

def minimax(board, depth, alpha, beta, maximizingPlayer, max_player):
    global memoization
    board_key = str(board.grid)
    if depth == 0 or board.check_victory():
            return [-1, board.score_position(max_player)]
    if (board_key, depth, maximizingPlayer) in memoization:
        return memoization[(board_key, depth, maximizingPlayer)]

    validLocations = board.get_possible_moves()
    isTerminal = board.check_victory() or (depth == 0)

    if isTerminal:
        if board.check_victory():
            if max_player == 1:
                result = [-1, float('-inf')]
            else:
                result = [-1, float('inf')]
        else:
            result = [-1, 0]
    else:
        if not validLocations:
            result = [0, 0]
        elif maximizingPlayer:
            value = float('-inf')
            column = validLocations[0]
            for col in validLocations:
                # Make the move
                board.add_disk(col, max_player, update_display=False)
                newScore = minimax(board, depth - 1, alpha, beta, False, max_player)[1]

                # Undo the move
                board.remove_disk(col)

                if newScore > value:
                    value = newScore
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            result = [column, value]
        else:
            value = float('inf')
            column = validLocations[0]
            for col in validLocations:
                # Make the move
                board.add_disk(col, 2 if max_player == 1 else 1, update_display=False)
                newScore = minimax(board, depth - 1, alpha, beta, True, max_player)[1]

                # Undo the move
                board.remove_disk(col)

                if newScore < value:
                    value = newScore
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            result = [column, value]

    memoization[(board_key, depth, maximizingPlayer)] = result
    return result


class Board:
    grid = np.array([[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]])
    WINDOW_LENGTH=4
    COLUMN_COUNT=7
    LINE_COUNT=6

    def eval(self, player):
        return self.score_position(player)

    def score_position(self, player):
        piece = player
        score = 0
        center_column = len(self.grid[0]) // 2
        center_array = [self.grid[i][center_column] for i in range(len(self.grid))]
        center_count = center_array.count(piece)
        score += center_count * 3

        for r in range(self.LINE_COUNT):
            for c in range(self.COLUMN_COUNT - self.WINDOW_LENGTH + 1):
                horizontal_window = self.grid[r][c:c + self.WINDOW_LENGTH]
                vertical_window = [self.grid[i][c] for i in range(r, r + self.WINDOW_LENGTH) if
                                   0 <= i < self.LINE_COUNT]
                if len(horizontal_window) == self.WINDOW_LENGTH:
                    score += self.evaluate_window(horizontal_window, piece)
                if len(vertical_window) == self.WINDOW_LENGTH:
                    score += self.evaluate_window(vertical_window, piece)

        for r in range(self.LINE_COUNT - self.WINDOW_LENGTH + 1):
            for c in range(self.COLUMN_COUNT - self.WINDOW_LENGTH + 1):
                if (r + self.WINDOW_LENGTH <= self.LINE_COUNT) and (c + self.WINDOW_LENGTH <= self.COLUMN_COUNT):
                    pos_slope_window = [self.grid[r + i][c + i] for i in range(self.WINDOW_LENGTH) if
                                        0 <= r + i < self.LINE_COUNT and 0 <= c + i < self.COLUMN_COUNT - self.WINDOW_LENGTH + 1]
                    if len(pos_slope_window) == self.WINDOW_LENGTH:
                        score += self.evaluate_window(pos_slope_window, piece)

        return score

    def remove_disk(self, column):
        for j in range(5, -1, -1):
            if self.grid[column][j] != 0:
                self.grid[column][j] = 0
                break

    def evaluate_window(self, window, piece):
        score = 0
        opp_piece = 1 if piece == 2 else 2

        my_count = np.count_nonzero(window == piece)
        opp_count = np.count_nonzero(window == opp_piece)
        empty_count = np.count_nonzero(window == 0)

        if my_count == 4:
            score += 100
        elif my_count == 3 and empty_count == 1:
            score += 10

        if opp_count == 3 and empty_count == 1:
            score -= 100

        if my_count == 2 and empty_count == 2:
            score += 5
        if opp_count == 2 and empty_count == 2:
            score -= 5

        # Center control
        center_column = len(self.grid[0]) // 2
        center_count = np.count_nonzero(window == piece)
        score += center_count * 3
        return score

    def copy(self):
        new_board = Board()
        new_board.grid = np.array(self.grid, copy=True)
        return new_board

    def reinit(self):
        self.grid.fill(0)
        for i in range(7):
            for j in range(6):
                canvas1.itemconfig(disks[i][j], fill=disk_color[0])

    def get_possible_moves(self):
        possible_moves = list()
        if self.grid[3][5] == 0:
            possible_moves.append(3)
        for shift_from_center in range(1, 4):
            if self.grid[3 + shift_from_center][5] == 0:
                possible_moves.append(3 + shift_from_center)
            if self.grid[3 - shift_from_center][5] == 0:
                possible_moves.append(3 - shift_from_center)
        return possible_moves

    def add_disk(self, column, player, update_display=True):
        for j in range(6):
            if self.grid[column][j] == 0:
                break
        self.grid[column][j] = player
        if update_display:
            canvas1.itemconfig(disks[column][j], fill=disk_color[player])

    def column_filled(self, column):
        return self.grid[column][5] != 0

    def check_victory(self):
        # Horizontal alignment check
        for line in range(6):
            for horizontal_shift in range(4):
                if self.grid[horizontal_shift][line] == self.grid[horizontal_shift + 1][line] == self.grid[horizontal_shift + 2][line] == self.grid[horizontal_shift + 3][line] != 0:
                    return True
        # Vertical alignment check
        for column in range(7):
            for vertical_shift in range(3):
                if self.grid[column][vertical_shift] == self.grid[column][vertical_shift + 1] == \
                        self.grid[column][vertical_shift + 2] == self.grid[column][vertical_shift + 3] != 0:
                    return True
        # Diagonal alignment check
        for horizontal_shift in range(4):
            for vertical_shift in range(3):
                if self.grid[horizontal_shift][vertical_shift] == self.grid[horizontal_shift + 1][vertical_shift + 1] ==\
                        self.grid[horizontal_shift + 2][vertical_shift + 2] == self.grid[horizontal_shift + 3][vertical_shift + 3] != 0:
                    return True
                elif self.grid[horizontal_shift][5 - vertical_shift] == self.grid[horizontal_shift + 1][4 - vertical_shift] ==\
                        self.grid[horizontal_shift + 2][3 - vertical_shift] == self.grid[horizontal_shift + 3][2 - vertical_shift] != 0:
                    return True
        return False


class Connect4:

    def __init__(self):
        self.board = Board()
        self.human_turn = False
        self.turn = 1
        self.players = (0, 0)
        self.ai_move = Queue()

    def current_player(self):
        return 2 - (self.turn % 2)

    def launch(self):
        self.board.reinit()
        self.turn = 0
        information['fg'] = 'black'
        information['text'] = "Turn " + str(self.turn) + " - Player " + str(
            self.current_player()) + " is playing"
        self.human_turn = False
        self.players = (combobox_player1.current(), combobox_player2.current())
        self.handle_turn()

    def move(self, column):
        if not self.board.column_filled(column):
            self.board.add_disk(column, self.current_player())
            self.handle_turn()

    def click(self, event):
        if self.human_turn:
            column = event.x // row_width
            self.move(column)

    def ai_turn(self, ai_level):
        Thread(target=alpha_beta_decision, args=(self.board, self.turn, ai_level, self.ai_move, self.current_player(),)).start()
        self.ai_wait_for_move()

    def ai_wait_for_move(self):
        if not self.ai_move.empty():
            self.move(self.ai_move.get())
        else:
            window.after(100, self.ai_wait_for_move)

    def handle_turn(self):
        self.human_turn = False
        if self.board.check_victory():
            information['fg'] = 'red'
            information['text'] = "Player " + str(self.current_player()) + " wins !"
            return
        elif self.turn >= 42:
            information['fg'] = 'red'
            information['text'] = "This a draw !"
            return
        self.turn = self.turn + 1
        information['text'] = "Turn " + str(self.turn) + " - Player " + str(
            self.current_player()) + " is playing"
        if self.players[self.current_player() - 1] != 0:
            self.human_turn = False
            self.ai_turn(self.players[self.current_player() - 1])
        else:
            self.human_turn = True


game = Connect4()

# Graphical settings
width = 700
row_width = width // 7
row_height = row_width
height = row_width * 6
row_margin = row_height // 10

window = tk.Tk()
window.title("Connect 4")
canvas1 = tk.Canvas(window, bg="blue", width=width, height=height)

# Drawing the grid
for i in range(7):
    disks.append(list())
    for j in range(5, -1, -1):
        disks[i].append(canvas1.create_oval(row_margin + i * row_width, row_margin + j * row_height, (i + 1) * row_width - row_margin,
                            (j + 1) * row_height - row_margin, fill='white'))


canvas1.grid(row=0, column=0, columnspan=2)

information = tk.Label(window, text="")
information.grid(row=1, column=0, columnspan=2)

label_player1 = tk.Label(window, text="Player 1: ")
label_player1.grid(row=2, column=0)
combobox_player1 = ttk.Combobox(window, state='readonly')
combobox_player1.grid(row=2, column=1)

label_player2 = tk.Label(window, text="Player 2: ")
label_player2.grid(row=3, column=0)
combobox_player2 = ttk.Combobox(window, state='readonly')
combobox_player2.grid(row=3, column=1)

combobox_player1['values'] = player_type
combobox_player1.current(0)
combobox_player2['values'] = player_type
combobox_player2.current(6)

button2 = tk.Button(window, text='New game', command=game.launch)
button2.grid(row=4, column=0)

button = tk.Button(window, text='Quit', command=window.destroy)
button.grid(row=4, column=1)

# Mouse handling
canvas1.bind('<Button-1>', game.click)

window.mainloop()
