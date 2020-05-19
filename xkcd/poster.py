import random, sys, json, xkcd
sys.path.insert(0, '..')
from pyfb.pyfb import PyFb

CACHE = xkcd.get_cache()

def get_post_content():
	latest_comic_num = int(xkcd.get_latest_from_cache(CACHE)['num'])
	chosen_num = random.randint(1, latest_comic_num)
	print('Picking comic, 1 <= {} <= {}'.format(chosen_num, latest_comic_num))
	comic = xkcd.get_comic(chosen_num, CACHE)
	content = '#{} Title: {}\nAlt:{}'.format(comic['num'], comic['safe_title'], comic['alt'])
	if 'transcript' in comic.keys() and len(comic['transcript']) > 0:
		content += '\nTranscript:{}'.format(comic['transcript'])
	return content