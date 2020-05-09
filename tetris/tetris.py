# modified from https://gist.github.com/silvasur/565419/d9de6a84e7da000797ac681976442073045c74a4
from random import randrange as rand
import random
import sys
from PIL import Image, ImageDraw

# The configuration
config = {
	'cell_size':	20,
	'cols':		8,
	'rows':		16,
	'delay':	750,
}

colors = [
(0,   0,   0  ),
(255, 0,   0  ),
(0,   150, 0  ),
(0,   0,   255),
(255, 120, 0  ),
(255, 255, 0  ),
(180, 0,   255),
(0,   220, 220),
(255, 255, 255),
(127, 0, 127)
]

for i in range(len(colors)):
	old_color = colors[i]
	colors[i] = (255 - old_color[0], 255 - old_color[1], 255 - old_color[2])

# Define the shapes of the single parts
tetris_shapes = [
	[[1, 1, 1],
	 [0, 1, 0]],
	
	[[0, 2, 2],
	 [2, 2, 0]],
	
	[[3, 3, 0],
	 [0, 3, 3]],
	
	[[4, 0, 0],
	 [4, 4, 4]],
	
	[[0, 0, 5],
	 [5, 5, 5]],
	
	[[6, 6, 6, 6]],
	
	[[7, 7],
	 [7, 7]]
]

SPECIAL_TETRIS_SHAPES = [
	[[8, 8, 8, 8],
	 [8, 7, 7, 8],
	 [8, 7, 7, 8],
	 [8, 8, 8, 8]],
	[[9, 0, 9],
	 [9, 9, 9],
	 [9, 0, 9]],
	[[8, 8, 8, 8],
	 [8, 0, 0, 8],
	 [8, 0, 0, 8],
	 [8, 8, 8, 8]],
	[[8, 8, 8, 8],
	 [0, 0, 0, 8],
	 [8, 8, 8, 8],
	 [8, 8, 8, 8]],
]

MOVES = ('drop', 'left', 'right', 'rotate', 'hard-drop', 'swap')
UNKNOWN = 'UNKNOWN'

def points_for_lines_cleared(lines_cleared):
	if lines_cleared <= 0:
		return 0
	return (2**(lines_cleared - 1)) * 100


def rotate_clockwise(shape):
	return [ [ shape[y][x]
			for y in range(len(shape)) ]
		for x in range(len(shape[0]) - 1, -1, -1) ]

def rotate_counter_clockwise(shape):
	for i in range(2):
		shape = rotate_clockwise(shape)
	return rotate_clockwise(shape)

def check_collision(board, shape, offset):
	off_x, off_y = offset
	for cy, row in enumerate(shape):
		for cx, cell in enumerate(row):
			try:
				if cell and board[ cy + off_y ][ cx + off_x ]:
					return True
			except IndexError:
				return True
	return False

def remove_row(board, row):
	del board[row]
	return [[0 for i in range(config['cols'])]] + board
	
def join_matrixes(mat1, mat2, mat2_off):
	off_x, off_y = mat2_off
	for cy, row in enumerate(mat2):
		for cx, val in enumerate(row):
			mat1[cy+off_y-1	][cx+off_x] += val
	return mat1

def new_board():
	board = [ [ 0 for x in range(config['cols']) ]
			for y in range(config['rows']) ]
	return board

def print_board(board):
	for row in board:
		for col in row:
			print(col, end='')
		print()

class TetrisState:
	def __init__(self):
		self.gameover = False
		self.score = 0
		self.special_countdown_timer = random.randint(12, 36)
		self.init_game()

	def rand_stone(self):
		return tetris_shapes[rand(len(tetris_shapes))]

	def rand_stone_special(self):
		return random.choice(SPECIAL_TETRIS_SHAPES)
	
	def new_stone(self):
		try: 
			self.next_stone
		except AttributeError:
			self.next_stone = None

		if self.next_stone is None:
			self.next_stone = self.rand_stone()
		self.stone = self.next_stone
		self.special_countdown_timer -= 1

		if self.special_countdown_timer > 0:
			self.next_stone = self.rand_stone()
		else:
			self.next_stone = self.rand_stone_special()
			self.special_countdown_timer = random.randint(12, 36)

		self.set_stonecoords()
		# compute stone color
		self.stone_color = colors[0]
		for row in self.stone:
			for col in row:
				if col > 0:
					self.stone_color = colors[col]
					break
		
		if check_collision(self.board,
		                   self.stone,
		                   (self.stone_x, self.stone_y)):
			self.gameover = True
	
	def set_stonecoords(self):
		self.stone_x = int(config['cols'] / 2 - len(self.stone[0])/2)
		self.stone_y = 0

	def init_game(self):
		self.board = new_board()
		self.new_stone()

	def swap(self):
		temp = self.stone
		self.stone = self.next_stone
		self.next_stone = temp
		self.set_stonecoords()
		return self

	def parse_move(self, move):
		move = move.strip().lower()
		if move == 'left':
			return self.left()
		elif move == 'right':
			return self.right()
		elif move == 'drop':
			return self.drop()
		elif move == 'rotate':
			return self.rotate_stone()
		elif move == 'hard-drop':
			return self.hard_drop()
		elif move == 'swap':
			return self.swap()
		else:
			return UNKNOWN
	
	def move(self, delta_x):
		if not self.gameover:
			new_x = self.stone_x + delta_x
			if new_x < 0:
				new_x = 0
			if new_x > config['cols'] - len(self.stone[0]):
				new_x = config['cols'] - len(self.stone[0])
			collision = check_collision(self.board, self.stone, 
				(new_x, self.stone_y))
			if not collision:
				self.stone_x = new_x
			self.check_lines_for_being_cleared()
			return collision

	def check_lines_for_being_cleared(self):
		lines_cleared = 0
		while True:
			for i, row in enumerate(self.board):
				if 0 not in row:
					self.board = remove_row(self.board, i)
					lines_cleared += 1
					break
			else:
				break
		self.score += points_for_lines_cleared(lines_cleared)

	def left(self):
		return self.move(-1)

	def right(self):
		return self.move(1)
	
	def drop(self):
		created_new_stone = False
		if not self.gameover:
			self.stone_y += 1
			if check_collision(self.board,
			                   self.stone,
			                   (self.stone_x, self.stone_y)):
				self.board = join_matrixes(
				  self.board,
				  self.stone,
				  (self.stone_x, self.stone_y))
				self.new_stone()
				self.check_lines_for_being_cleared()
				created_new_stone = True
		return created_new_stone

	def hard_drop(self):
		ns = False
		while not(self.gameover) and not(ns):
			ns = self.drop()
	
	def rotate_stone(self):
		collision = True
		self.check_lines_for_being_cleared()
		if not self.gameover:
			new_stone = rotate_counter_clockwise(self.stone)
			collision = check_collision(self.board,
			                       new_stone,
			                       (self.stone_x, self.stone_y))
			if not collision:
				self.stone = new_stone
		return collision

	def to_image(self, out, bg=None, xoff=0):
		img = None
		cell_size = config['cell_size']
		if bg is None:
			img = Image.new('RGB', (config['cols']*config['cell_size'], 
				config['rows']*config['cell_size']))
		else:
			img = Image.open(bg)
			xoff += img.size[0] // 4
			cell_size = img.size[1] // config['rows']
		draw = ImageDraw.Draw(img)
		for y in range(len(self.board)):
			for x in range(len(self.board[y])):
				color = colors[self.board[y][x]]
				draw.rectangle([xoff + x*cell_size, y*cell_size,
					xoff+(x+1)*cell_size, (y+1)*cell_size], fill=color, outline=(200, 200, 200))

		for y in range(len(self.stone)):
			for x in range(len(self.stone[y])):
				if self.stone[y][x] == 0: 
					continue
				color = colors[self.stone[y][x]]
				_x = x + self.stone_x
				_y = y + self.stone_y
				draw.rectangle([xoff+_x*cell_size, _y*cell_size,
					xoff+(_x+1)*cell_size, (_y+1)*cell_size], fill=color, outline=(0, 0, 0))

		xoff += (config['cols'] + 2) * config['cell_size']
		print(self.next_stone)
		for y in range(len(self.next_stone)):
			for x in range(len(self.next_stone[y])):
				color = colors[self.next_stone[y][x]]
				_x = x
				_y = y #+ config['cell_size']
				print(xoff+_x*cell_size)
				draw.rectangle([xoff+_x*cell_size, _y*cell_size,
					xoff+(_x+1)*cell_size, (_y+1)*cell_size], fill=color, outline=(0, 0, 0))				
		img.save(out)
	def random_moves(self, count):
		for _ in range(count):
			if self.gameover:
				break
			self.parse_move(random.choice(MOVES))
			self.drop()

	def rows_between_stone_and_top(self):
		stone_bot_y = self.stone_y + len(self.stone)
		empty_rows = 0
		for y in range(stone_bot_y, len(self.board)):
			if max(self.board[y]) == 0:
				empty_rows += 1
			else:
				break
		return empty_rows

	def drop_close_gap(self):
		did_extra_drops = False
		stone_height = len(self.stone)
		stone_width = len(self.stone[0])
		min_gap = max(stone_height, stone_width)
		while not(self.gameover) and self.rows_between_stone_and_top() > min_gap:
			self.drop()
			did_extra_drops = True
		return did_extra_drops

