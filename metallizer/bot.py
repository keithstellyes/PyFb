import random, sys, json
sys.path.insert(0, '..')
from pyfb.pyfb import PyFb
import metallizer

fb_client = PyFb(json.load(open('../tokens.json', 'r'))['metal'])

if __name__ == '__main__':
	text, photo_path = metallizer.make_post()
	post_id = fb_client.create_post(message=text, image_path=photo_path)['post_id']

