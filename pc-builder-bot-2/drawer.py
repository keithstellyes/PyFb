from ddgimageapi import dl_first_image
import model
from PIL import Image, ImageDraw
import sys
sys.path.insert(0, '..')
from angusphotos.ap import random_angus_photo_file_path

def do_img(query):
	filename = dl_first_image(query, 'tmp.png')[0]
	if filename is None:
		print('could not get an image for', query, 'using a placeholder angus pic')
		return Image.open(random_angus_photo_file_path())
	return Image.open(filename)

def draw_pc_mosaic(pc):
	parts = []
	parts.append(do_img(model.pstr_case(pc.case)))
	parts.append(do_img(model.pstr_cpu(pc.cpu)))
	parts.append(do_img(model.pstr_mobo(pc.mobo)))
	i = 0
	for m in pc.memory.keys():
		parts.append(do_img(model.pstr_memory(m)))
	for s in pc.storage.keys():
		parts.append(do_img(model.pstr_storage(s)))
	tile_size = parts[0].size[1] // len(parts[1:])
	out = Image.new('RGB', (parts[0].size[0] + tile_size, parts[0].size[1]))
	out.paste(parts[0], (0, 0))
	side_parts = parts[1:]
	for i in range(len(side_parts)):
		sp = side_parts[i]
		ratio = sp.size[0] / sp.size[1]
		sp = sp.resize((int(ratio * tile_size), tile_size))
		out.paste(sp, (parts[0].size[0], i * tile_size))
	out.save('tmp-out.png')
	return 'tmp-out.png'
