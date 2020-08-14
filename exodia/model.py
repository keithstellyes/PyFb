import json, random, requests
import toml
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Boolean, SmallInteger, LargeBinary
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy.sql import exists
from sqlalchemy import func
import ygo

Base = declarative_base()
ENGINE = create_engine('sqlite:///exodia.db')
ASSERT_DECK_SIZE_40 = True
ASSERT_HAS_EXODIA = True
EXODIA_HAND = sorted(tuple(['Exodia the Forbidden One', 'Left Leg of the Forbidden One', 'Left Arm of the Forbidden One',
	'Right Leg of the Forbidden One', 'Right Arm of the Forbidden One']))

YGO_WIDTH = 421
YGO_HEIGHT = 614

CARD_NAME_LEN = 256

class Card(Base):
	__tablename__ = 'cards'
	name = Column(String(CARD_NAME_LEN), primary_key=True)
	image_url = Column(String(1024))

class Deck(Base):
	__tablename__ = 'decks'
	name = Column(String(256))
	id = Column(Integer, primary_key=True)

	def create_entry(self, card_name, quantity):
		return DeckEntry(deck_id=self.id, card_name=card_name, quantity=quantity)

	def get_contents(self):
		session = Session()
		q = session.query(DeckEntry).filter(DeckEntry.deck_id == self.id)
		return q.all()

	def draw_five(self):
		session = Session()
		cards = []
		for entry in self.contents:
			cards = cards + [entry.card_name] * entry.quantity
		random.shuffle(cards)
		return tuple(cards[:5])

	def can_do_exodia(self):
		missing_cards = list(EXODIA_HAND)
		for e in self.contents:
			if len(missing_cards) == 0:
				return True
			if e.card_name in missing_cards:
				missing_cards.remove(e.card_name)
		return False

	contents = property(get_contents, None)

class DeckEntry(Base):
	__tablename__ = 'deckentries'
	deck_id = Column(Integer, ForeignKey('decks.id'), primary_key=True)
	card_name = Column(String(CARD_NAME_LEN), ForeignKey('cards.name'), primary_key=True)
	quantity = Column(Integer)

class UrlData(Base):
	__tablename__ = 'urldata'
	url = Column(String(2048), primary_key=True)
	data = Column(LargeBinary())

class Post(Base):
	__tablename__ = 'posts'
	fb_post_id = Column(String(2048), primary_key=True)
	deck_id = Column(Integer, ForeignKey('decks.id'))
	# 5 cards, 2 quote chars and a space per card; plus 2 for opening and closing bracket
	hand_json = Column(String(CARD_NAME_LEN * 5 + (3 * 5) + 2))
	num_exodia_pieces = Column(Integer)

	def sanity(self):
		assert self.num_exodia_pieces >= 0 and self.num_exodia_pieces <= 5

	def from_fb_post_id_and_hand(fb_post_id, hand):
		assert len(hand) == 5
		p = Post()
		p.fb_post_id = fb_post_id
		p.hand_json = json.dumps(hand)
		exodia_cards = []
		for c in hand:
			if c in EXODIA_HAND:
				exodia_cards.append(c)
		p.num_exodia_pieces = len(set(exodia_cards))
		return p
def next_deck_id():
	last_id = Session().query(func.max(Deck.id)).scalar()
	if last_id is None:
		return 0
	return last_id + 1

def dl_url(url, filename):
	session = Session()
	data = session.query(UrlData.data).filter(UrlData.url == url).scalar()
	if data is not None:
		print(url, 'already in db')
		with open(filename, 'wb') as f:
			f.write(data)
	else:
		print(url, 'not already in db, downloading')
		r = requests.get(url, stream=True)
		with open(filename, 'wb') as f:
		    for chunk in r.iter_content(chunk_size=1024): 
		        if chunk:
		            f.write(chunk)
		f = open(filename, 'rb')
		session.add(UrlData(url=url, data=f.read()))
		f.close()
		session.commit()


def load_deck(deck_filepath):
	data = toml.load(open(deck_filepath, 'r'))
	deck = Deck()
	deck.name = data['_name']
	card_names = [k for k in data.keys() if not k.startswith('_')]

	### checking deck looks OK ###
	total_cards = 0
	for n in card_names:
		assert data[n] > 0
		total_cards = total_cards + data[n]
	assert not(ASSERT_DECK_SIZE_40) or total_cards == 40

	session = Session()
	deck = Deck()
	deck.id = next_deck_id()
	for card_name in card_names:
		if not session.query(exists().where(Card.name == card_name)).scalar():
			card = Card()
			card.name = card_name
			print(card_name, 'not already in db, grabbing image')
			card.image_url = random.choice(ygo.get_card_images(card_name))
			print('using {} for card {}'.format(card.image_url, card.name))
			session.add(card)
			session.commit()
		session.add(deck.create_entry(card_name, data[card_name]))
	session.commit()

def hands_equal(h0, h1):
	return sorted(h0) == sorted(h1)

def deck_exodia_sim(deck):
	assert deck.can_do_exodia()
	tries = 0
	while True:
		tries = tries + 1
		if hands_equal(deck.draw_five(), EXODIA_HAND):
			return tries

Base.metadata.create_all(ENGINE)
Session = sessionmaker(bind=ENGINE)