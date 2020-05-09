import json, os, sys

this_dir = os.path.dirname(os.path.abspath(__file__)) + '/'
parent_dir = '/'.join(this_dir.split('/')[:-1]) + '/'
DEFAULT_TOKEN_PATH = parent_dir + 'tokens.json'

token_path = DEFAULT_TOKEN_PATH
if len(sys.argv) > 1:
	token_path = sys.argv[1]

token_data = json.load(open(token_path, 'r'))
print('token path:', token_path)
key = input('token key:')
value = input('token value:')

print(key, '=', value)
if key in token_data.keys():
	print('NOTE {} is already in token file'.format(key))
is_ok = input('Is this ok? [y/n] ').lower() == 'y'

if is_ok:
	print('Token is OK, saving')
	token_data[key] = value
	# sort_keys, indent=2 for pretty reading
	json.dump(token_data, open(token_path, 'w'), sort_keys=True, indent=2)
else:
	print('Token is NOT OK, exiting.')