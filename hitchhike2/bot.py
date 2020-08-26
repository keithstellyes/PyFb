import random, sys, json
sys.path.insert(0, '..')
from pyfb.pyfb import PyFb
import mapper, model, hh
from sqlalchemy.sql import exists
import time
import geocoder

fb_client = PyFb(json.load(open('../tokens.json', 'r'))['hh'])
CONFIG = json.load(open('config.json', 'r'))

def new_route(session):
	r = model.Route()
	default_origin = CONFIG['routes']['default origin']
	default_dest = CONFIG['routes']['default destination']
	origin = mapper.place_search(default_origin)
	dest = mapper.place_search(default_dest)
	if origin is None or dest is None:
		if origin is None:
			print('Could not find origin', default_origin)
		if dest is None:
			print('Could not find dest', default_dest)
		sys.exit(1)
	r.origin = origin.osm_id
	r.dest = dest.osm_id

	model.add_place_if_not_exists(origin, session)
	model.add_place_if_not_exists(dest, session)
	session.add(r)
	session.commit()
	rs = model.RouteStep()
	rs.route_id = r.id
	rs.route_step = 0 
	rs.place = r.origin
	session.add(rs)
	session.commit()

	return r

def new_route_post():
	session = model.Session()
	r = new_route(session)
	origin = session.query(model.Place).filter(model.Place.osm_id == r.origin).one()
	dest = session.query(model.Place).filter(model.Place.osm_id == r.dest).one()
	do_post(CONFIG['messages']['new route'].format(origin=origin.name, dest=dest.name) + CONFIG['messages']['suffix'], origin, 
		r.id, 0, session)
	session.commit()

def comment_map(fb_post_id):
	pass

def do_post(message, place, route_id, route_step, session):
	success = hh.create_pano(hh.get_pano_id(place.lat, place.lon))
	new_post = model.Post(route_id=route_id, route_step=route_step)

	mapper.map_places(model.current_route().places_visited())
	if success:
		post = fb_client.create_360_photo_post(message=message, image_path='pano.jpg')
		new_post.fb_post_id = post['post_id'].split('_')[-1]
	else:
		new_post.fb_post_id = fb_client.create_post(message='Failed to do street view ' + CONFIG['messages']['suffix'], image_path='map.png')['post_id']
	session.add(new_post)
	return new_post

def step():
	current_route = model.current_route()
	max_dist = CONFIG['routes']['max distance']
	prefix = CONFIG['messages']['request prefix']
	if current_route is None:
		print('No routes found, doing first route ever')
		new_route_post()
	elif current_route.is_completed():
		print('Current route completed! Doing new route...')
		new_route_post()
	else:
		print('Current route not completed!')
		curr_step = model.current_step()
		curr_place = model.current_place()
		session = model.Session()
		fb_post_id = session.query(model.Post.fb_post_id)\
			.filter(model.Post.route_id == current_route.id)\
			.filter(model.Post.route_step == curr_step.route_step)\
			.scalar()
		print('Latest post ID:', fb_post_id)
		comments = [c for c in fb_client.get_post_comments(fb_post_id)]
		print('COMMENTS:', comments)
		reqs = {}
		for comment in comments:
			user = comment['from']
			msg = comment['message']
			if msg.lower().startswith(prefix.lower()):
				req = model.Request()
				req.post_id = fb_post_id
				req.comment_id = comment['id']
				req.user_id = user['id']
				req.query = msg[len(prefix):].strip()
				if not session.query(exists().where(model.Request.comment_id == req.comment_id)).scalar():
					session.add(req)
				# avoid duplicate requests
				reqs[req.user_id] = req
		chosen_req = None
		chosen_place = None
		reqs = list(reqs.values())
		random.shuffle(reqs)
		for req in reqs:
			place = mapper.place_search(req.query)
			if place is None:
				fb_client.comment_on_post(post_id=req.comment_id, message="Failed to find '{}' on Nominatim (Open Street Map)".format(req.query))
				print(req.query, 'cant be found')
			elif model.distance_between_places(place, curr_place) > max_dist:
				fb_client.comment_on_post(post_id=req.comment_id, message='Too far, must be within {} {}'.format(max_dist, model.measurement()))
				print(req.query, 'is too far')
			elif chosen_req is None:
				fb_client.comment_on_post(post_id=req.comment_id, message='Sure! Let\'s go there!')
				chosen_req = req
				current_route.step(place, session)
				chosen_place = place
			else:
				fb_client.comment_on_post(post_id=req.comment_id, message='I parsed this and found it, but not going here, sorry :(')
		origin_place = session.query(model.Place.name).filter(model.Place.osm_id == current_route.origin).one().name
		dest_place = session.query(model.Place.name).filter(model.Place.osm_id == current_route.dest).one().name
		if chosen_place is None:
			print('couldnt pick a place, so no post')
			return
		msg = CONFIG['messages']['route step'].format(curr_place=chosen_place.name, origin=origin_place, dest=dest_place) + CONFIG['messages']['suffix']
		post = do_post(msg, chosen_place, current_route.id, curr_step.route_step + 1, session)
		session.commit()
		suggested_places = []
		for attraction in geocoder.osm('attraction near [{lat}, {lon}]'.format(lat=chosen_place.lat, lon=chosen_place.lon), maxRows=10):
			try:
				suggested_places.append(attraction)
			except KeyError:
				print('No display_name for:', attraction.json)
		message = 'Here are some attractions nearby!\n'
		message += '* ' + '\n* '.join([r.json['raw']['display_name'] for r in suggested_places])
		fb_client.comment_on_post(post_id=post.fb_post_id, message=message)

if __name__ == '__main__':
	step()
