import os, random
this_path = os.path.dirname(os.path.abspath(__file__)) + '/'
angus_path = this_path + 'angus/'

def random_angus_photo_file_path():
	photos = os.listdir(angus_path)
	return angus_path + random.choice(photos)