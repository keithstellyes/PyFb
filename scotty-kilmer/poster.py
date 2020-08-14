import random, sys, json
sys.path.insert(0, '..')
from pyfb.pyfb import PyFb
import model, videocardgen

fb_client = PyFb(json.load(open('../tokens.json', 'r'))['scotty'])

def post(thumbnail_url, title):
	videocardgen.draw_card(thumbnail_url, title)
	fb_client.create_post(message=title, image_path='tmp-card.png')

if __name__ == '__main__':
	post(model.random_video().thumbnail, model.do_chain())