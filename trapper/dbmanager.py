import csv, sqlite3, sys, random

IMAGE_URL = 'http://ids.si.edu/ids/deliveryService?id=emammal_image_{seqid}i{count}&max=1000'
DEFAULT_PATH = 'trapper.db'

class Animal:
	def __init__(self, id, common_name, species_name):
		self.id = id
		self.common_name = common_name
		self.species_name = species_name
	def __str__(self):
		return 'Animal[id={} {}({})]'.format(self.id, self.common_name, self.species_name)
class Project:
	def __init__(self, id, name):
		self.id = id
		self.name = name

class Subproject:
	def __init__(self, id, name, parent):
		self.id = id
		self.name = name
		self.parent = parent

class Photo:
	def __init__(self, id, seqid, animal, subproject, lat, lon, count):
		self.id = id
		self.seqid = seqid
		self.animal = animal
		self.subproject = subproject
		self.lat = lat
		self.lon = lon
		self.count = count

	def get_image_urls(self):
		urls = []
		for i in range(1, self.count + 1):
			urls.append(IMAGE_URL.format(seqid=self.seqid, count=i))
		return urls

	def __str__(self):
		return 'Photo[id={} animal={}]'.format(self.id, self.animal)

def get_animal_by_id(conn, id):
	cursor = conn.cursor()
	cursor.execute('SELECT id, commonName, speciesName FROM Animals WHERE id=? LIMIT 1;', (id,))
	animal = cursor.fetchall()[0]
	return Animal(*animal)

def get_project_by_id(conn, id):
	cursor = conn.cursor()
	cursor.execute('SELECT id, name FROM Projects WHERE id=? LIMIT 1;', (id,))
	project = cursor.fetchall()[0]
	return Project(*project)

def get_subproject_by_id(conn, id):
	cursor = conn.cursor()
	cursor.execute('SELECT id, name, parentId FROM Subprojects WHERE id=? LIMIT 1;', (id,))
	subproject = list(cursor.fetchall()[0])
	subproject[2] = get_project_by_id(conn, subproject[2])
	return Subproject(*subproject)

def get_photo_by_id(conn, id):
	cursor = conn.cursor()
	cursor.execute('SELECT id, seqid, animalId, subprojectId, lat, lon, count FROM Photos WHERE id=? LIMIT 1;', (id,))
	photo = list(cursor.fetchall()[0])
	photo[2] = get_animal_by_id(conn, photo[2])
	photo[3] = get_subproject_by_id(conn, photo[3])
	return Photo(*photo)

def get_db(path=DEFAULT_PATH):
	return sqlite3.connect(path)

def db_init(conn):
	cursor = conn.cursor()
	cursor.execute('CREATE TABLE IF NOT EXISTS Projects(name TEXT, id INTEGER);')
	cursor.execute('CREATE TABLE IF NOT EXISTS Subprojects(name TEXT, id INTEGER, parentId INTEGER);')
	cursor.execute('CREATE TABLE IF NOT EXISTS Animals(id INTEGER, commonName TEXT, speciesName TEXT);')
	cursor.execute('CREATE TABLE IF NOT EXISTS Photos(id INTEGER, seqId INTEGER, animalId INTEGER, subprojectId INTEGER, lat TEXT, lon TEXT, count INTEGER);')
	cursor.execute('CREATE TABLE IF NOT EXISTS CreatedPosts(postId TEXT, photoId INTEGER, timestamp INTEGER, answered INTEGER)')

	conn.commit()

def get_random_id(conn, tablename):
	return random.randint(0, get_next_id(conn, tablename) - 1)

def get_random_photo(conn):
	return get_photo_by_id(conn, get_random_id(conn, 'Photos'))

def get_next_id(conn, tablename):
	cursor = conn.cursor()
	cursor.execute('SELECT MAX(id) FROM {} LIMIT 1;'.format(tablename))
	last = cursor.fetchone()[0]
	if last is not None:
		return last + 1
	return 0

def get_subproject_id(conn, name, parent_id):
	cursor = conn.cursor()
	cursor.execute('SELECT id FROM Subprojects WHERE name=? AND parentId=?', (name, parent_id))
	id = cursor.fetchone()
	if id is not None:
		return id[0]
	print('New subproject: {} of parent ID {}'.format(name, parent_id))
	id = get_next_id(conn, 'Subprojects')
	cursor.execute('INSERT INTO Subprojects(name, id, parentId) VALUES(?, ?, ?)', (name, id, parent_id))
	conn.commit()

def get_project_id(conn, project_name):
	cursor = conn.cursor()
	cursor.execute('SELECT id FROM Projects WHERE name=?', (project_name,))
	id = cursor.fetchone()
	if id is not None:
		return id[0]
	print('New project:', project_name)
	id = get_next_id(conn, 'Projects')
	cursor.execute('INSERT INTO Projects(name, id) VALUES(?, ?)', (project_name, id))
	conn.commit()

def get_animal_id(conn, common_name, species_name):
	cursor = conn.cursor()
	cursor.execute('SELECT id FROM Animals WHERE commonName=? AND speciesName=?', (common_name, species_name,))
	id = cursor.fetchone()
	if id is not None:
		return id[0]
	print('New animal: {} ({})'.format(common_name, species_name))
	id = get_next_id(conn, 'Animals')
	cursor.execute('INSERT INTO Animals(commonName, speciesName, id) VALUES(?, ?, ?)', (common_name, species_name, id))
	conn.commit()

def get_photo_id(conn, seqid, animal_id, subproject_id, lat, lon, count):
	cursor = conn.cursor()
	# note, a seqid refers to the photos, but if a photo has multiple 
	cursor.execute('SELECT id FROM PHOTOS WHERE seqId=? AND subprojectid=? AND animalId=?', 
		(seqid, subproject_id, animal_id))
	id = cursor.fetchone()
	if id is not None:
		print('Old photo seqid={} subproject_id={} animal_id={}'.format(seqid, subproject_id, animal_id))
		return id[0]
	id = get_next_id(conn, 'Photos')
	print('New photo! id={} seqid={}'.format(id, seqid))
	cursor.execute('INSERT INTO Photos(id, seqId, animalId, subprojectId, lat, lon, COUNT) VALUES(?, ?, ?, ?, ?, ?, ?)',
		(id, seqid, animal_id, subproject_id, lat, lon, count))

def add_in_csv(conn, path):
	with open(path, 'r') as f:
		reader = csv.reader(f)
		rows = [r for r in reader]
		assert rows[0] == ['Project', 'Subproject', 'Treatment', 'Deployment Name', 
			'ID Type', 'Deployment ID', 'Sequence ID', 'Begin Time', 'End Time', 'Species Name', 
			'Common Name', 'Age', 'Sex', 'Individually Identifiable', 'Count', 'Actual Lat', 'Actual Lon', 'Fuzzed']
		cursor = conn.cursor()
		for row in rows[1:]:
			project_name = row[0]
			subproject_name = row[1]
			seqid = row[6]
			species_name = row[9]
			common_name = row[10]
			count = int(row[14])
			lat = row[15]
			lon = row[16]

			project_id = get_project_id(conn, project_name)
			subproject_id = get_subproject_id(conn, subproject_name, project_id)
			animal_id = get_animal_id(conn, common_name, species_name)
			get_photo_id(conn, seqid, animal_id, subproject_id, lat, lon, count)
		conn.commit()
if __name__ == '__main__':
	conn = get_db()
	db_init(conn)
	for path in sys.argv[1:]:
		add_in_csv(conn, path)