import sys
sys.path.insert(0, '..')
from pyfb.pyfb import PyFb
import jeopardy, jeopardytitle, random, sqlite3, json
from datetime import datetime

def add_questions_to_db(db_client, count):
	questions = jeopardy.get_questions_succinct(count)
	cursor = db_client.cursor()
	questions_added = 0
	for q in questions:
		# find if question already exists
		cursor.execute('SELECT id FROM Questions WHERE id=? LIMIT 1', (q['id'],))
		if len(cursor.fetchall()) > 0:
			print('Got an already seen question, skipping')
			continue
		cursor.execute('INSERT INTO Questions(id, question, answer, category, json)' +
			'VALUES(?, ?, ?, ?, ?)', 
			(q['id'], q['question'], q['answer'], q['category'], q['json']))
	db_client.commit()
	return questions_added

def unused_questions(db_client):
	cursor = db_client.cursor()
	cursor.execute('SELECT id, question, answer, category FROM Questions WHERE id NOT IN(SELECT questionId FROM CreatedPosts)')
	return [{'id':row[0], 'question':row[1], 'answer':row[2], 'category':row[3]} for row in cursor.fetchall()]

def last_post(db_client):
	cursor = db_client.cursor()
	cursor.execute('SELECT postId, questionId FROM CreatedPosts ORDER BY ts DESC LIMIT 1')
	try:
		return [r for r in cursor.fetchall()][0]
	except IndexError:
		return None

def last_answer(db_client):
	cursor = db_client.cursor()
	lp = last_post(db_client)
	if lp is None:
		return None
	last_post_id = lp[0]
	last_question_id = lp[1]
	cursor.execute('SELECT answer FROM Questions WHERE id=? LIMIT 1', (last_question_id,))
	return [r for r in cursor.fetchall()][0][0]

def make_post(db_client, fb_client, question):
	jeopardytitle.make_title_card(question['question'], 'out.png')
	post_id = fb_client.create_post('Answer posted when this is an hour old.\nCATEGORY: ' +
		  question['category'], 'out.png')['post_id']
	db_client.cursor().execute('INSERT INTO CreatedPosts(postId, questionId, ts) ' +
		'VALUES(?, ?, ?)', (post_id, question['id'], int(datetime.now().timestamp())))
	db_client.commit()

def iteration(db_client, fb_client):
	# get unused question count
	unused_qs = unused_questions(db_client)
	unused_question_count = 0
	if unused_qs is not None:
		unused_question_count = len(unused_qs)
	print('Unused question count:', unused_question_count)
	if unused_question_count < 400:
		print('Deciding to pull more questions')
		add_questions_to_db(db_client, 100)
		unused_qs = unused_questions(db_client)
	lp = last_post(db_client)
	la = last_answer(db_client)
	if lp is not None:
		print('Found last post id:', lp[0], 'the answer was:', la)
		fb_client.comment_on_post(lp[0], 'The answer was: ' + la)
	else:
		print('No latest post found!')

	print('Making new post!')
	chosen_question = random.choice(unused_qs)
	while chosen_question['question'].strip() == '':
		chosen_question = random.choice(unused_qs)
	print('Chose the question:', str(chosen_question))
	make_post(db_client, fb_client, chosen_question)

if __name__ == '__main__':
	db_client = sqlite3.connect('jeopardy.db')
	fb_client = PyFb(json.load(open('../tokens.json', 'r'))['jeopardy'])
	iteration(db_client, fb_client)