import random, requests, sqlite3, json, html

CONN = sqlite3.connect('photos.db')
# XML because their JSON endpoint is weird
API_URL = 'http://metallizer.dk/api/json/0'

def random_photo_from_db():
	c = CONN.cursor()
	c.execute('SELECT copyright, data FROM PHOTOS')
	photos = c.fetchall()
	random.shuffle(photos)
	photo = photos[0]
	photos = None # help GC out
	f = open('tmp.jpg', 'wb')
	f.write(photo[1])
	return photo[0], 'tmp.jpg'

def random_album():
	r = requests.get(API_URL)
	if r.status_code != 200:
		raise Exception('Metallizer return non-200 status code!')
	t = r.text
	t = t.lstrip('jsonMetallizerAlbum(')
	html_result = json.loads(t.rstrip(');'))
	return {k : html.unescape(v) for k, v in html_result.items()}

def album_pstr(album):
	head = '{} by {}'.format(album['album'], album['artist']) + '\n'
	tracks = []
	for i in range(len(album['tracks'])):
		tracks.append('{}. {}'.format(i + 1, album['tracks'][i]))
	return head + '\n' + '\n'.join(tracks)

def make_post():
	al = random_album()
	text = album_pstr(al)
	copyright, photo_path = random_photo_from_db()
	text += '\nPhoto copyright: {}; Album generated by metallizer.dk'.format(copyright)
	return text, photo_path