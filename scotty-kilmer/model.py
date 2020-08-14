import random
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Boolean, SmallInteger, LargeBinary
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy.sql import exists
from sqlalchemy import func, update

Base = declarative_base()
ENGINE = create_engine('sqlite:///scotty.db')

class Video(Base):
	__tablename__ = 'videos'
	id = Column(String(32), primary_key=True)
	title = Column(String(2048))
	thumbnail = Column(String(2048))

# You are now entering... THE MARKOV ZONE
class Word(Base):
	__tablename__ = 'words'
	id = Column(Integer(), primary_key=True)
	# longest word in English: pneumonoultramicroscopicsilicovolcanoconiosis, 45 chars
	contents = Column(String(64))

	def sanity(self):
		assert (self.id == 0 and self.contents is None) or (self.id != 0 and self.contents is not None)

	def __str__(self):
		return '<Word id={} "{}">'.format(self.id, self.contents)

class Transition(Base):
	__tablename__ = 'transitions'
	word_1 = Column(Integer(), ForeignKey('words.id'), primary_key=True)
	word_2 = Column(Integer(), ForeignKey('words.id'), primary_key=True)
	occurrences = Column(Integer())

	def __str__(self):
		return '<Transition {} => {} {}x>'.format(self.word_1, self.word_2, self.occurrences)

	def __repr__(self):
		return str(self)

Base.metadata.create_all(ENGINE)
Session = sessionmaker(bind=ENGINE)
session = Session()

def next_word_id():
	return Session().query(func.max(Word.id)).scalar() + 1

# True if word was added, False not added (if it didn't already exist, for example)
def add_word(word):
	if word is None:
		return False
	session = Session()
	if not session.query(exists().where(Word.contents == word)).scalar():
		session.add(Word(id=next_word_id(), contents=word))
		session.commit()
		return True
	return False

def get_word(word):
	if word is None:
		return Word(id=0, contents=None)
	session = Session()
	result = session.query(Word).filter(Word.contents == word).scalar()
	return result

def add_transition(w0, w1):
	add_word(w0)
	add_word(w1)
	w0 = get_word(w0)
	w1 = get_word(w1)
	t = session.query(Transition).filter(Transition.word_1 == w0.id).filter(Transition.word_2 == w1.id).scalar()
	if t is None:
		t = Transition(word_1=w0.id, word_2=w1.id, occurrences=0)
		session.add(t)
		session.commit()
	t.occurrences = t.occurrences + 1
	session.commit()

def add_sentence(sentence):
	words = sentence.split(' ')
	for i in range(len(words)):
		w0 = words[i]
		w1 = None
		if i + 1 < len(words):
			w1 = words[i + 1]
		add_transition(w0, w1)

def consume_videos_text(path):
	FIELDS = ('title', 'id', 'thumbnail')
	video = Video()
	index = 0
	for line in open(path, 'r'):
		line = line.strip()
		field = FIELDS[index]
		index = (index + 1) % len(FIELDS)
		if field == 'title':
			video.title = line
		elif field == 'id':
			video.id = line
		elif field == 'thumbnail':
			video.thumbnail = line
			if not (session.query(exists().where(Video.id == video.id)).scalar()):
				session.add(video)
				add_sentence(video.title)
			video = Video()
	session.commit()

def random_word():
	session = Session()
	word = None
	highest_word_id = session.query(func.max(Word.id)).scalar()
	while word is None:
		id = random.randint(1, next_word_id())
		word = session.query(Word).filter(Word.id == id).scalar()
	return word

def random_video():
	return random.choice(Session().query(Video).all())

def do_chain(seed_word=None):
	curr_word = None
	if seed_word is None:
		curr_word = random_word()
	else:
		curr_word = get_word(seed_word)

	session = Session()
	words = []
	while curr_word.id != 0:
		words.append(curr_word.contents)
		transitions = session.query(Transition).filter(Transition.word_1 == curr_word.id).all()
		total = sum([t.occurrences for t in transitions])
		die_roll = random.randint(0, total)
		running_total = 0
		for t in transitions:
			running_total += t.occurrences
			if running_total >= die_roll:
				curr_word = session.query(Word).filter(Word.id == t.word_2).scalar()
				break
	return ' '.join(words)

if not session.query(exists().where(Word.id == 0)).scalar():
	print("Don't already have the NULL word, adding...")
	session.add(Word(id=0, contents=None))
	session.commit()