import sys, json
sys.path.insert(0, '..')
from pyfb.pyfb import PyFb

data = json.load(open(sys.argv[1], 'r'))
image_path = sys.argv[2]

fb_client = PyFb(json.load(open('../tokens.json', 'r'))['electoralcollege'])
red_votes = sum(data['red'].values())
blue_votes = sum(data['blue'].values())
rc = data['candidates']['red']
rc = rc[:rc.index('.')]
bc = data['candidates']['blue']
bc = bc[:bc.index('.')]

winning_candidate = rc if red_votes > blue_votes else bc
losing_candidate = rc if red_votes < blue_votes else bc
winner_votes = red_votes if red_votes > blue_votes else blue_votes

pid = fb_client.create_post(message='{} has beaten {} with {} votes'.format(winning_candidate, losing_candidate, winner_votes),
	image_path=image_path)['post_id']

fb_client.comment_on_post(message='Nothing says good logging like a Facebook comment: ' + json.dumps(data),
	post_id=pid)