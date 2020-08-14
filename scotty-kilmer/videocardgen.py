import requests
from PIL import Image, ImageDraw, ImageFont
import model

def dl_url(url, filename):
	r = requests.get(url)
	with open(filename, 'wb') as f:
	    for chunk in r.iter_content(chunk_size=1024): 
	        if chunk:
	            f.write(chunk)

def draw_card(thumbnail_url, title):
	dl_url(thumbnail_url, 'tmp-thumbnail')
	thumbnail = Image.open('tmp-thumbnail')
	title_height = int(thumbnail.size[1] / 6)
	bg = Image.new('RGB', (thumbnail.size[0], thumbnail.size[1] + title_height), color='#282828')
	bg.paste(thumbnail, (0, 0))
	draw = ImageDraw.Draw(bg)
	font_size = 60
	font = ImageFont.truetype('./Roboto-Regular.ttf', font_size)
	while font.getsize(title)[0] > thumbnail.size[0] + 25 + 5:
		font_size -= 5
		font = ImageFont.truetype('./Roboto-Regular.ttf', font_size)
	draw.text((25, thumbnail.size[1] + 25), title, font=font)
	bg.save('tmp-card.png')