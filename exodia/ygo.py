import json, requests

URL = 'https://db.ygoprodeck.com/api/v7/cardinfo.php'

def get_card_images(card_name):
	r = requests.get(URL, params={'name':card_name})
	if r.status_code != 200:
		raise Exception('Card name: {} not found'.format(card_name))
	return [item['image_url'] for item in json.loads(r.text)['data'][0]['card_images']]