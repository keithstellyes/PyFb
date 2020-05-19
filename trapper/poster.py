import random, sys, json, dbmanager
sys.path.insert(0, '..')
from pyfb.pyfb import PyFb
from pyfb.util import accept_answer
from datetime import datetime
import requests, time

headers = {'User-Agent':json.load(open('../tokens.json', 'r'))['trapper/fb-url']}

def get_post_content(db):
	sleep_time = 1
	while True:
		try:
			photo = dbmanager.get_random_photo(db)
			message = 'CREDIT eMammal; from {}\n'.format(photo.subproject.parent.name)
			url = random.choice(photo.get_image_urls())
			dl_image(url, 'out', headers=headers)
			return message, photo, url
		except Exception as e:
			print('got', e, 'sleeping then trying another photo, sleeping for {}'.format(sleep_time))
			time.sleep(sleep_time)
			# don't dos them our friends at the Smithsonian
			sleep_time = sleep_time * 2

def dl_image(url, filename, headers):
	r = requests.get(url, headers=headers)

	if r.status_code == 200:
		with open(filename, 'wb') as f:
			f.write(r.content)
	else:
		raise Exception("didn't get 200 resp on downloading " + url)

def do_answers(fb_client, db):
	post_id, photo_id, answered = db.cursor().execute('SELECT postId, photoId, answered FROM CreatedPosts ORDER BY timestamp DESC LIMIT 1').fetchall()[0]
	answered = answered == 1
	if answered:
		print('Already answered on postId {}'.format(post_id))
		return
	photo = dbmanager.get_photo_by_id(db, photo_id)
	animal = photo.animal
	fb_client.comment_on_post(post_id=post_id, message='Answer: common name: "{}" species name: "{}"\nLAT,LON: {},{}'.format(
		animal.common_name, animal.species_name, photo.lat, photo.lon))
	db.cursor().execute('UPDATE CreatedPosts SET answered=1 WHERE postId=?', (post_id,))
	db.commit()

def get_fb_client():
	return PyFb(json.load(open('../tokens.json', 'r'))['trapper'])

if __name__ == '__main__':
	db = dbmanager.get_db()
	message, photo, url = None, None, None
	if sys.argv[1] == 'debug' or sys.argv[1] == 'q':
		message, photo, url = get_post_content(db)

	if sys.argv[1] == 'debug':
		print(message, photo, url)
	elif sys.argv[1] == 'q':
		fb_client = get_fb_client()
		pid = fb_client.create_post(message=message, image_path='out')['post_id']
		ts = int(datetime.now().timestamp())
		db.cursor().execute('INSERT INTO CreatedPosts(postId, photoId, timestamp) VALUES(?, ?, ?)',
			(pid, photo.id, ts))
		db.commit()
	elif sys.argv[1] == 'a':
		do_answers(get_fb_client(), db)