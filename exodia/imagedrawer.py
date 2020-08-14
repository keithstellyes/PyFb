from PIL import Image, ImageDraw
import model

def draw_hand(bg_path, hand, out_path='out.png'):
	session = model.Session()
	image_urls = []
	for c in hand:
		image_urls.append(session.query(model.Card.image_url).filter(model.Card.name == c).scalar())

	bg = Image.open(bg_path)
	card_width = int(bg.size[0] / (5 + 6 * .25))
	card_height = int(model.YGO_HEIGHT // (model.YGO_WIDTH / card_width))
	print(card_width, card_height)
	x, y = (card_width // 4, bg.size[1] // 4)
	for i in range(len(image_urls)):
		url = image_urls[i]
		fname = 'tmp-img-' + str(i)
		model.dl_url(url, fname)
		card_image = Image.open(fname)
		card_image = card_image.resize((card_width, card_height))
		bg.paste(card_image, (x, y))
		x = int(x + card_width * 1.25)
	bg.save(out_path)

if __name__ == '__main__':
	#draw_hand('bg.jpg', model.Deck(id=0).draw_five())
	draw_hand('bg.jpg', model.EXODIA_HAND, out_path='exodia-hand.png')