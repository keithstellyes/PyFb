import json, os, requests, sqlite3

CACHE_PATH = this_dir = os.path.dirname(os.path.abspath(__file__)) + '/' + 'xkcd.db'
LATEST_COMIC_URL = 'https://xkcd.com/info.0.json'
SPECIFIC_COMIC_URL = 'https://xkcd.com/{}/info.0.json'

def dl_image(url, filename):
	r = requests.get(url, timeout=0.5)

	if r.status_code == 200:
		with open(filename, 'wb') as f:
			f.write(r.content)
	else:
		raise Exception("didn't get 200 resp on downloading " + url)

def get_cache(path=CACHE_PATH):
	return sqlite3.connect(path)

def cache_init(cache):
	# we're being a bit lazy and just loading it in as a blob (ideally, we would be parsing the JSON
	# and having columns like num, transcript, image path, etc.. In a case like this it also might
	# make more sense to use something like mongodb in place of sqlite, but I want to
	# keep things simple, and sqlite3 is built-in into Python and doesn't require config
	cache.cursor().execute('CREATE TABLE IF NOT EXISTS Comics(num INTEGER, blob TEXT);')
	cache.commit()

def write_comic_to_cache(comic, cache):
	cache.cursor().execute('INSERT INTO Comics(num, blob) VALUES(?, ?);', (comic['num'], json.dumps(comic)))
	cache.commit()

# returns the image path, also ensures that it actually already has an image
def ensure_comic_image_path(comic):
	url = comic['img']
	#We don't know what the extension will be, sometimes png, sometimes jpg...
	target_image_path = '{}{}'.format(comic['num'], url[url.rindex('.'):])
	if not os.path.exists(target_image_path):
		print(comic['num'], 'not already downloaded, downloading...')
		dl_image(url, target_image_path)
	return target_image_path

def get_comic_from_url(url):
	r = requests.get(url)
	if r.status_code != 200:
		raise Exception('request status not 200: {}, text: {}'.format(r, r.text))
	return json.loads(r.text)

def get_latest_comic(cache):
	comic = get_comic_from_url(LATEST_COMIC_URL)
	cursor = cache.cursor()
	cursor.execute('SELECT COUNT(num) FROM Comics WHERE num=?;', (comic['num'],))
	count = cursor.fetchone()[0]
	if count == 0:
		print('Latest comic cache MISS, writing to cache')
		write_comic_to_cache(comic, cache)
	else:
		print('Latest comic cache HIT')
	return comic

def get_latest_from_cache(cache):
	cursor = cache.cursor()
	cursor.execute('SELECT blob FROM Comics ORDER BY num DESC LIMIT 1;')
	return json.loads(cursor.fetchone()[0])

def get_comic(num, cache):
	cursor = cache.cursor()
	cursor.execute('SELECT blob FROM Comics WHERE num=? LIMIT 1;', (int(num),))
	latest = cursor.fetchone()
	if latest is None:
		print(num, 'cache MISS, downloading comic and will write to cache')
		comic = get_comic_from_url(SPECIFIC_COMIC_URL.format(num))
		write_comic_to_cache(comic, cache)
		return comic
	else:
		print(num, 'cache HIT, reading from cache')
		return json.loads(latest[0])

# make it easy for a cronjob to grab latest say, every 12 hours
if __name__ == '__main__':
	print('Latest comic!')
	print(get_latest_comic(get_cache()))