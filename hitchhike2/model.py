from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Boolean, SmallInteger, LargeBinary
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy.sql import exists
from sqlalchemy import func
import json, requests
import requests_cache
import geopy.distance
requests_cache.install_cache('cache')

Base = declarative_base()
ENGINE = create_engine('sqlite:///hh.db')
CONFIG = json.load(open('config.json', 'r'))

class Place(Base):
	__tablename__ = 'places'
	name = Column(String(1024), nullable=False)
	lat = Column(String(32), nullable=False)
	lon = Column(String(32), nullable=False)
	osm_id = Column(String(37), primary_key=True)

def distance_between_places(pa, pb):
	dist = geopy.distance.distance((pa.lat, pa.lon), (pb.lat, pb.lon))
	if CONFIG['miles']:
		return dist.miles
	else:
		return dist.km

class Route(Base):
	__tablename__ = 'routes'
	id = Column(Integer(), primary_key=True)
	origin = Column(String(37), ForeignKey('places.osm_id'))
	dest = Column(String(37), ForeignKey('places.osm_id'))

	def step(self, place):
		session = Session()
		rs = RouteStep()
		rs.route_id = self.id
		rs.route_step = current_step().route_step + 1
		rs.place = place.osm_id
		session.add(rs)
		add_place_if_not_exists(place, session)
		session.commit()

	def places_visited(self):
		session = Session()
		return session.query(Place)\
			.join(RouteStep)\
			.filter(RouteStep.route_id == self.id)\
			.filter(RouteStep.place == Place.osm_id)\
			.order_by(RouteStep.route_step.asc())\
			.all()

	def pstr(self):
		lines = [p.name for p in self.places_visited()]
		lines[0] = 'START: '  + lines[0]
		lines[-1] = 'CURRENT: ' + lines[-1]
		return '\n'.join(lines)

	def is_completed(self):
		last_place = self.places_visited()[-1]
		dest_place = Session().query(Place).filter(Place.osm_id == self.dest).one()
		return distance_between_places(last_place, dest_place) <= CONFIG['routes']['completion radius']

class RouteStep(Base):
	__tablename__ = 'routesteps'
	route_id = Column(Integer(), ForeignKey('routes.id'), primary_key=True)
	route_step = Column(Integer(), primary_key=True)
	place = Column(String(37), ForeignKey('places.osm_id'))

class Post(Base):
	__tablename__ = 'posts'
	route_id = Column(Integer(), ForeignKey('routes.id'))
	route_step = Column(Integer(), nullable=False)
	fb_post_id = Column(String(64), primary_key=True)

class Request(Base):
	__tablename__ = 'requests'
	post_id = Column(String(64), ForeignKey('posts.fb_post_id'))
	comment_id = Column(String(64), primary_key=True)
	user_id = Column(String(64), nullable=False)
	query = Column(String(2048), nullable=False)

def current_route():
	session = Session()
	id = session.query(func.max(Route.id)).scalar()
	if id is None:
		return None
	return session.query(Route).filter(Route.id == id).one()

def current_step():
	route = current_route()
	if route is None:
		return None
	session = Session()
	current_step = session.query(func.max(RouteStep.route_step)).filter(RouteStep.route_id == route.id).scalar()
	return session.query(RouteStep).filter(RouteStep.route_id == route.id).filter(RouteStep.route_step == current_step).one()

def current_place():
	step = current_step()
	if step is None:
		return None
	session = Session()
	return session.query(Place).filter(Place.osm_id == step.place).one()

def add_place_if_not_exists(place, session):
	if not session.query(exists().where(Place.osm_id == place.osm_id)).scalar():
		session.add(place)
		session.commit()

def measurement():
	return 'miles' if CONFIG['miles'] else 'km'

Base.metadata.create_all(ENGINE)
Session = sessionmaker(bind=ENGINE)