import json, os, random, requests, subprocess

GMAPS_API_KEY = json.load(open('../tokens.json', 'r'))["gapi/hb66"]
def get_pano_id(lat, lon, do_off=False, epsilon=.0003):
	lat = float(lat)
	lon = float(lon)
	# epsilon is a bit of a hack. Basically, the exact coordinates of major points of interests
	# will often have a user-submitted street view photo, which I still haven't figured out how to grab.
	# SO, what we try to do instead if we can't use it, is to offset it by a very small epsilon,
	# and hopefully it'll still be really close to the point of interest, and hopefully it'll still
	# be visible.
	if do_off:
		lat = lat - random.uniform(-epsilon, epsilon)
		lon = lon - random.uniform(-epsilon, epsilon)
	headers = {'Content-Type': 'application/json',}

	params = (
    ('location', '{}, {}'.format(lat, lon)),
	('key', GMAPS_API_KEY),
	('radius', '500')
	)

	response = requests.get('https://maps.googleapis.com/maps/api/streetview/metadata', headers=headers, params=params)
	data = response.json()
	if str(response.json()['status']) != "OK":
		print(response.json())
		return None
	else:
		pano_id = str(response.json()['pano_id'])
		# user submitted, likely won't work with later logic
		if pano_id.startswith('CAoS'):
			return get_pano_id(lat, lon, do_off=True)
		return pano_id

def dl_url(url, filename):
	r = requests.get(url, stream=True)
	if r.status_code != 200:
		raise Exception('status code is {}, resp:{}'.format(r.status_code, r.text))
	with open(filename, 'wb') as f:
	    for chunk in r.iter_content(chunk_size=1024): 
	        if chunk:
	            f.write(chunk)

def set_image_exif(image_path='pano.jpg'):
	subprocess.run(['exiftool', '-ProjectionType=equirectangular', 'pano.jpg'])


# GMAP_PANO_URL = 'http://cbk0.google.com/cbk?output=tile&panoid={}&zoom=5&x=[00-25]&y=[00-12]'
GMAP_PANO_URL = 'http://cbk0.google.com/cbk?output=tile&panoid={panoid}&zoom=5&x={x:02}&y={y:02}'
def create_pano(panoid):
	try:
		os.mkdir('tmpdir')
	except FileExistsError:
		pass
	#subprocess.run(['curl', GMAP_PANO_URL.format(panoid), '-o', "tmpdir/tile_y#2-x#1.jpg"])
	for x in range(0, 26):
		for y in range(0, 13):
			try:
				dl_url(GMAP_PANO_URL.format(panoid=panoid, x=x, y=y), 'tmpdir/tile_y{y:02}-x{x:02}.jpg'.format(y=y, x=x))
			except Exception as e:
				print(e)
				return False
	subprocess.run(['gm', 'montage', '+frame', '+shadow', '-tile', '26x13', '-geometry', '400x400+0+0', "tmpdir/tile_*.jpg", "pano.jpg"])
	set_image_exif()
	return True

'''
name=$1
currentDir=$(pwd)/$name
url='http://cbk0.google.com/cbk?output=tile&panoid='$1'&zoom=5&x=[00-25]&y=[00-12]'
tile='tile_y#2-x#1.jpg'
echo "create dir:"$currentDir
mkdir -p "$currentDir"
echo "downloading"
curl $url -o "$currentDir/$tile"
echo "creating pano"
gm montage +frame +shadow -tile 26x13 -geometry 400x400+0+0 "$currentDir/tile_*.jpg" "$currentDir.jpg"

'''