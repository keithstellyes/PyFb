import os, sqlite3, sys, json, random
from datetime import datetime

sys.path.insert(0, '..')
from pyfb.pyfb import PyFb
from pyfb.util import accept_answer
from angusphotos import ap
import wheresangus


this_dir = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = this_dir + '/wheresangus.db'

DO_FLAG_QUESTION_RATE = 0.25

def thing_happens(rate):
	assert rate >= 0.0 and rate <= 1.0
	return random.random() < rate

class Db:
	def __init__(self, db_path=DEFAULT_DB_PATH):
		self.conn = sqlite3.connect(db_path)
		self.cursor = self.conn.cursor()
		self.init_db()

	def init_db(self):
		self.cursor.execute('CREATE TABLE IF NOT EXISTS Posts(postId TEXT, timestamp INTEGER, answer TEXT, photo TEXT)')
		self.cursor.execute('CREATE TABLE IF NOT EXISTS Answers(userId TEXT, postId TEXT, givenAnswer TEXT)')

	def record_post(self, post_id, answer, photo):
		self.cursor.execute('INSERT INTO Posts(postId, timestamp, answer, photo) VALUES(?, ?, ?, ?)', 
			(post_id, int(datetime.now().timestamp()), answer, photo))
		self.conn.commit()

	def latest_post(self):
		self.cursor.execute('SELECT postId, answer FROM Posts ORDER BY timestamp DESC LIMIT 1')
		try:
			return self.cursor.fetchall()[0]
		except:
			return None
	def get_user_num_correct_answers(self, user_id):
		self.cursor.execute('SELECT COUNT(postId) FROM Answers WHERE userId=?', (user_id,))
		try:
			return self.cursor.fetchall()[0][0]
		except:
			return 0
	def record_correct_answer(self, user_id, post_id, given_answer):
		self.cursor.execute('INSERT INTO Answers(userId, postId, givenAnswer) VALUES(?, ?, ?)', 
			(user_id, post_id, given_answer))
		self.conn.commit()

	def get_leaderboard_top10(self):
		self.cursor.execute('select userId, COUNT(*) as times FROM answers GROUP BY userId ORDER BY times DESC LIMIT 10;')
		try:
			return [_ for _ in self.cursor.fetchall()]
		except:
			return []

def make_post_content():
	factbook = wheresangus.get_factbook()
	if thing_happens(DO_FLAG_QUESTION_RATE):
		return '', 'out-flag.png', wheresangus.random_flag(factbook)
	else:
		q, a = wheresangus.random_question(factbook)
		q = q.replace(a, 'COUNTRY')
		photo = ap.random_angus_photo_file_path()
		post_text = q + '\n({})'.format(photo.split('/')[-1])
		return post_text, photo, a

def get_fb_client():
	return PyFb(json.load(open('../tokens.json', 'r'))['wheresangus'])

def get_db_client():
	return Db()

def do_post(post_text, photo, a, fb_client, db_client):
	post_id = fb_client.create_post(message=post_text, image_path=photo)['post_id']
	db_client.record_post(post_id=post_id, answer=a, photo=photo)

def clean_answer_tests():
	eqs = [['South KOREA', 'Korea, South'], ['America', 'america'], ['bahamas', 'bahamas, the'], ['Pitcairn Island', 'Pitcairn Islands']]
	for w1, w2 in eqs:
		assert accept_answer(w1, (w2,))
	china_names = wheresangus.names(wheresangus.get_factbook()['countries']['china']).split('|')
	print(china_names)
	accept_answer('People\'s Republic of China', china_names)
	accept_answer('CHINA!!', china_names)
	accept_answer('PRC', china_names)

def do_answers(fb_client, db_client):
	post_id, answers = db_client.latest_post()
	answers = answers.split('|')
	correct_users = {}
	for comment in fb_client.get_post_comments(post_id):
		user = comment['from']
		resp = comment['message']
		if user['id'] not in correct_users.keys() and accept_answer(resp, answers):
			correct_users[user['id']] = comment['id']
			db_client.record_correct_answer(user_id=user['id'], post_id=post_id, given_answer=resp)

	for correct_user in correct_users.keys():
		message = 'Correct! You have gotten {} questions right'.format(db_client.get_user_num_correct_answers(correct_user))
		fb_client.comment_on_post(post_id=correct_users[correct_user], message=message)

	leaderboards = db_client.get_leaderboard_top10()
	message = 'The potential answers were {}'.format(answers)
	pos = 1
	if leaderboards is not None and len(leaderboards) > 0:
		for row in leaderboards:
			user_name = row[0]
			num_answers = row[1]
			try:
				user_name = fb_client.get_username_for_user_id(row[0])
			except Exception as e:
				pass
			message += '\n{}. {} has {} correct answers!'.format(pos, user_name, num_answers)
			pos += 1
	fb_client.comment_on_post(post_id=post_id, message=message)

if __name__ == '__main__':
	post_text, photo, a = None, None, None
	if sys.argv[1] in ('debug', 'doquestion'):
		post_text, photo, a = make_post_content()
	if len(sys.argv) != 2:
		print('Need a mode!')
		print('MODES: debug, doquestion, doanswers, test')
		sys.exit(1)
	elif sys.argv[1] == 'debug':
		print('================')
		print(post_text)
		print('================')
		print('answer: ', a)
	elif sys.argv[1] == 'doquestion':
		do_post(post_text, photo, a, fb_client=get_fb_client(), db_client=get_db_client())
	elif sys.argv[1] == 'doanswer':
		do_answers(db_client=get_db_client(), fb_client=get_fb_client())
	elif sys.argv[1] == 'test':
		clean_answer_tests()
