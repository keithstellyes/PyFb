import sys, json
sys.path.insert(0, '..')

from pyfb.pyfb import PyFb
from angusphotos import ap
import wheresangus

def make_post_content():
	factbook = wheresangus.get_factbook()
	q, a = wheresangus.random_question(factbook)
	photo = ap.random_angus_photo_file_path()
	post_text = q + '\n({})'.format(photo.split('/')[-1])
	return post_text, photo, a

def get_fb_client():
	return PyFb(json.load(open('../tokens.json', 'r'))['wheresangus'])

def do_post(post_text, photo, a, fb_client):
	fb_client.create_post(message=post_text, image_path=photo)

if __name__ == '__main__':
	post_text, photo, a = make_post_content()
	if len(sys.argv) > 1 and sys.argv[1] == 'debug':
		print('================')
		print(post_text)
		print('================')
		print('answer: ', a)
	else:
		do_post(post_text, photo, a, fb_client=get_fb_client())