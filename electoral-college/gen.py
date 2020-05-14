import random, sys, json, os

votes = json.load(open('votes.json', 'r'))
red = {}
blue = {}
candidates = {}
output = {'votes':votes, 'red':red, 'blue':blue, 'candidates':candidates}
possible_candidates = list(os.listdir('candidates'))

for state in votes.keys():
	color = random.choice((red, blue))
	color[state] = votes[state]

if random.choice((True, False)):
	print('Landslide')
	print('Pre: red:{} blue:{}'.format(red, blue))
	victim = random.choice((red, blue))
	benefactor = None
	if victim == red:
		print('Victim: red')
		benefactor = blue
	else:
		print('Victim: blue')
		benefactor = red
	victim_states = [state for state in victim.keys() if random.choice((True, False))]
	assert victim != benefactor
	for state in victim_states:
		benefactor[state] = victim[state]
		del victim[state]
	print('Lost states:', victim_states)
else:
	print('No landslide')

random.shuffle(possible_candidates)
candidates['red'] = possible_candidates[0]
candidates['blue'] = possible_candidates[1]

json.dump(output, open('out.json', 'w'))