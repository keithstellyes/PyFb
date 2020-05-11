import os, sys, json, pickle, sqlite3, tetris
from datetime import datetime

sys.path.insert(0, '..')

from pyfb.pyfb import PyFb

REACTION_TO_MOVE_MAP = {'LOVE':'left', 'HAHA':'right',
	'WOW':'rotate', 'LIKE':'drop', 'ANGRY':'hard-drop', 'SAD':'swap'}

def consume_file(path):
	exists = os.path.exists(path)
	if exists:
		os.remove(path)
	return exists

class TetrisBot:
	def __init__(self):
		self.fb_client = PyFb(json.load(open('../tokens.json', 'r'))['tetris'])
		self.db_client = sqlite3.connect('tetris.db')

	# returns id, tetris state
	def read_latest_state(self):
		cursor = self.db_client.cursor()
		cursor.execute('SELECT id, state FROM CreatedPosts ORDER BY ts DESC LIMIT 1')
		row = [_ for _ in cursor.fetchall()][0]
		return row[0], pickle.loads(row[1])

	def write_state(self, tetris_state, msg_prefix=''):
		ts = int(datetime.now().timestamp())
		## TODO: hardcoded! very naughty...
		#bg = 'angus.jpeg
		bg = 'angus2.jpg'
		tetris_state.to_image('out.png', bg=bg)
		msg = msg_prefix + 'React to vote on a move!\n❤️ Left\t😂 Right\t😮 Rotate\t👍 Down\t😡 Hard drop\t😢 Swap'
		post_id = self.fb_client.create_post(msg, 'out.png')['post_id']
		self.db_client.cursor().execute('INSERT INTO CreatedPosts(id, state, ts) VALUES(?, ?, ?)',
			(post_id, pickle.dumps(tetris_state), ts))
		self.db_client.commit()
		return post_id

	def new_state(self):
		print('Starting over and writing it!')
		g = tetris.TetrisState()
		g.drop()
		g.drop()
		g.drop()
		self.write_state(g, msg_prefix='NEW GAME!\n')

if __name__ == '__main__':
	tb = TetrisBot()
	print('Reading latest state')
	latest_post_id, tetris_state = None, None
	try:
		latest_post_id, tetris_state = tb.read_latest_state()
		try:
			tetris_state.score
		except AttributeError:
			tetris_state.score = 0
		try:
			tetris_state.special_countdown_timer
		except AttributeError:
			tetris_state.special_countdown_timer = 0
	except IndexError:
		# needs to be init'd.
		tb.new_state()
		sys.exit(0)
	print('Latest state found! Post ID: ' + str(latest_post_id))
	if tetris_state.gameover:
		print('Game over!')
		if not consume_file('stop-on-gameover'):
			tb.new_state()
		sys.exit(0)

	rtally = tb.fb_client.get_post_reaction_tally(latest_post_id)
	next_move = 'drop'
	max_react_count = 0
	for react in rtally:
		if rtally[react] > max_react_count and react in REACTION_TO_MOVE_MAP.keys():
			max_react_count = rtally[react]
			next_move = REACTION_TO_MOVE_MAP[react]
	result = tetris_state.parse_move(next_move)
	if (next_move == 'left' or next_move == 'right' or next_move == 'rotate') and result:
		tetris_state.drop()
	msg_prefix = 'SCORE: ' + str(tetris_state.score) + '\nSelected move: ' + next_move + '\n'
	if tetris_state.drop_close_gap():
		msg_prefix = '(Speeding things up...)' + msg_prefix
	pid = tb.write_state(tetris_state, msg_prefix=msg_prefix)
	print('Just posted! ' + pid)