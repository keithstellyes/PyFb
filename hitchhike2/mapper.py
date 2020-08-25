import json, requests
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap as Basemap
from matplotlib.colors import rgb2hex, Normalize
from matplotlib.patches import Polygon
from matplotlib.collections import LineCollection
import geocoder, requests_cache
import geopy.distance

import model

requests_cache.install_cache('cache')

CONFIG = json.load(open('config.json', 'r'))
# for km -> set it to false
USING_MILES = CONFIG["miles"]

SPACE_NEEDLE_OSM_ID = 'W12903132'
# geocoder doesn't support it it semms :/
def look_up_osm_id(osm_id, email):
	r = requests.get('https://nominatim.openstreetmap.org/lookup', params={'osm_ids':osm_id, 'email':email, 'format':'json'})
	return json.loads(r.text)[0]

def place_search(query):
	try:
		search = geocoder.osm(query)[0].json
		p = model.Place()
		p.name = query.strip()
		p.lat = search['lat']
		p.lon = search['lng']
		osm_id = str(search['osm_id'])
		if search['osm_type'] == 'way':
			osm_id = 'W' + osm_id
		elif search['osm_type'] == 'node':
			osm_id = 'N' + osm_id
		elif search['osm_type'] == 'relation':
			osm_id = 'R' + osm_id
		else:
			print('Unrecognized OSM type', search['osm_type'])
		p.osm_id = osm_id
		return p
	except IndexError:
		return None # no results

def get_map():
	fig, ax = plt.subplots()
	m = Basemap(llcrnrlon=-119,llcrnrlat=20,urcrnrlon=-64,urcrnrlat=49,
            projection='lcc',lat_1=33,lat_2=45,lon_0=-95, width=1920, height=1080, ax=ax)
	m.readshapefile('st99_d00','states',drawbounds=True,
                           linewidth=0.45,color='gray')
	m.drawmapboundary(fill_color='aqua')
	m.fillcontinents(color='coral',lake_color='aqua')

	for nshape,seg in enumerate(m.states):
	    poly = Polygon(seg,facecolor=CONFIG["landcolor"],edgecolor='#000000')
	    ax.add_patch(poly)
	return m, fig, ax

def map_places(places):
	m, fig, ax = get_map()
	points = [m(p.lon, p.lat) for p in places]
	names = [p.name for p in places]
	for i in range(len(places)):
		#lon, lat = points[i]
		name = names[i][:CONFIG["points"]["max name length"]]
		#xpt, ypt = m(lon, lat)
		xpt, ypt = points[i]
		m.plot(xpt, ypt, 'bo', markersize=CONFIG['points']['pointsize'])
		plt.text(xpt+CONFIG['points']['x offset'],ypt+CONFIG['points']['y offset'],name,fontsize=CONFIG['points']['fontsize'])

	lc_points = []
	for i in range(1, len(points)):
		lc_points.append((points[i - 1], points[i]))
	ax.add_collection(LineCollection(lc_points, color=CONFIG["route line color"]))
	plt.savefig('map.png', dpi=CONFIG["dpi"])

if __name__ == '__main__':
	route = (place_search('Seattle'), place_search('Tacoma'), place_search('Portland, Oregon'), 
		place_search('Los Angeles'), place_search('Phoenix'), place_search('Austin'),
		place_search('New Orleans'), place_search('Atlanta, Georgia'), place_search('Miami, Florida'))
	map_places(route)