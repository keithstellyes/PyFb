import json, os, random, requests, sqlite3, zipfile
import cairosvg
from SPARQLWrapper import SPARQLWrapper, JSON

this_dir = os.path.dirname(os.path.abspath(__file__))
FACTBOOK_PATH = this_dir + '/factbook.json'
WIKIDATA_PATH = this_dir + '/wikidata.json'

db_path = this_dir + '/wheresangus.db'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Question:
	def __init__(self, answer, message='', image_path=None):
		if type(answer) != str:
			raise ValueError("Answer must be a str")
		self.answer = answer
		self.message = message
		self.image_path = image_path
	def __str__(self):
		return '<Question answer="{}" message="{}" image_path="{}">'.format(self.answer, self.message, self.image_path)

def get_master():
	try:
		return json.load(open('master.json', 'r'))
	except FileNotFoundError:
		fb = get_factbook()
		wd = get_wikidata()
		results = {}
		fb_countries = fb['countries']
		for fb_country_k in fb_countries.keys():
			fb_country = fb_countries[fb_country_k]
			results[fb_country_k] = {'fb': fb_country}
			ccode = None
			try:
				ccode = fb_countries[fb_country_k]['data']['communications']['internet']['country_code'][:3]
			except KeyError:
				pass
			if ccode is not None:
				wd_found = False
				for wd_country_k in wd.keys():
					if wd_country_k == '_raw':
						continue
					if 'wd' in results[fb_country_k].keys():
						msg = 'Found duplicate TLD entry: curr {} {}'.format(fb_country_k, ccode)
						raise Exception(msg)
					if ccode in wd[wd_country_k]['tlds']:
						results[fb_country_k]['wd'] = wd[wd_country_k]
						wd_found = True
						break
				if not wd_found:
					print('Could not find wikidata for:', fb_country_k, ccode)
		json.dump(results, open('master.json', 'w'))
		return results

# http://wikidata.org/wiki/Wikidata:SPARQL_tutorial
# https://people.wikimedia.org/~bearloga/notes/wdqs-python.html
def get_wikidata():
	try:
		return json.load(open(WIKIDATA_PATH, 'r'))
	except FileNotFoundError:
		sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
		q = 'SELECT ?item ?countryId ?tlds ?tldsLabel ?mapImage ?coatOfArms WHERE {\n'
		q = q + '?item wdt:P31 wd:Q6256;\n'
		q = q + 'wdt:P297 ?countryId;\n'
		q = q + 'wdt:P78 ?tlds;\n'
		q = q + 'OPTIONAL {?item wdt:P242 ?mapImage.}\n'
		q = q + 'OPTIONAL {?item wdt:P237/wdt:P18 ?coatOfArms.}\n'
		q = q + 'SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }\n'
		q = q + '}'
		print(q)
		sparql.setQuery(q)
		sparql.setReturnFormat(JSON)
		raw_results = sparql.query().convert()

		results = {}
		for row in raw_results['results']['bindings']:
			id = row['countryId']['value'].lower()
			if id not in results.keys():
				results[id] = {}
				results[id]['mapImage'] = []
				try:
					results[id]['coatOfArms'] = row['coatOfArms']['value']
				except KeyError:
					print('No coat of arms for', id)
					pass
				results[id]['tlds'] = []
			results[id]['tlds'].append(row['tldsLabel']['value'])
			results[id]['tlds'] = list(set(results[id]['tlds']))
			results[id]['mapImage'].append(row['mapImage']['value'])
			results[id]['mapImage'] = list(set(results[id]['mapImage']))
		results['_raw'] = raw_results
		results = results
		json.dump(results, open(WIKIDATA_PATH, 'w'))
		return results

def dl_svg_as_png(url):
	with open('out.svg', 'w') as f:
		r = requests.get(url)
		f.write(r.text)
	cairosvg.svg2png(url='out.svg', write_to='out.png')
	return 'out.png'

def download_wikidata_svg(master, country_name, key):
	dl_svg_as_png(master[country_name]['wd'][key])
	return 'out.png'

def names(master, country):
	names = [master[country]['fb']['data']['name']]
	try:
		names = names + list(country['data']['government']['country_name'].values())
	except:
		pass
	return '|'.join(names)

# from https://github.com/iancoleman/cia_world_factbook_api
def get_factbook():
	return json.load(open(FACTBOOK_PATH, 'r'))

def q_intro_question(master, country_name):
	country = master[country_name]['fb']
	sents = country['data']['introduction']['background'].split('\n')[0].split('.')
	segment_begin_max = len(sents) - 2
	segment_begin = random.randint(0, segment_begin_max)
	intro = '.'.join(sents[segment_begin:(segment_begin + 2)])

	return Question(message=intro.replace(country['data']['name'], '[COUNTRY]'), answer=names(master, country_name))

def q_major_urban_areas(master, country_name):
	a = names(master, country_names)
	country = master[country_name]['fb']
	q = "The major urban areas of this country include: "
	urban_areas = [ua['place'] for ua in country['data']['people']['major_urban_areas']['places']]
	if len(urban_areas) == 1:
		return Question(message="The major urban area of this country is " + urban_areas[0], answer=a) 
	q += ', '.join(urban_areas[:-1])
	q += ' and ' + urban_areas[-1]
	return Question(message=q, answer=a)

def q_linguistic_makeup(master, country_name):
	country = master[country_name]['fb']
	q = "The linguistic makeup of this country is: "
	langs = []
	for lang in country['data']['people']['languages']['language']:
		lang_full = lang['name']
		if 'note' in lang.keys():
			lang_full += '({})'.format(lang['note'])
		langs.append(lang_full)
	q += ', '.join(langs)
	return Question(message=q, answer=names(master, country_name))

def q_location(master, country_name):
	country = master[country_name]['fb']
	q = "This country is in " + country['data']['geography']['location']
	return Question(message=q, answer=names(master, country_name))

def q_flag_description(master, country_name):
	country = master[country_name]['fb']
	q = "This country's flag "
	fd = country['data']['government']['flag_description']
	q += fd['description']
	if 'note' in fd.keys():
		q += '; ' + fd['note']
	return Question(message=q, answer=names(master, country_name))

# f_ fact
def f_current_environmental_issues(master, country_name):
	country = master[country_name]['fb']
	return 'environmental issues: ' + ','.join(country['data']['geography']['environment']['current_issues'])

def f_intl_environmental_agreements(master, country_name):
	country = master[country_name]['fb']
	s = 'party to the following international environmental agreements: ' 
	return s + ','.join(country['data']['geography']['environment']['international_agreements']['party_to'])

def f_climate(master, country_name):
	country = master[country_name]['fb']
	return 'climate: ' + country['data']['geography']['climate']

def f_hazards(master, country_name):
	country = master[country_name]['fb']
	return 'natural hazards: ' + ', '.join([h['description'] for h in country['data']['geography']['natural_hazards']])

def f_urban_population(master, country_name):
	country = master[country_name]['fb']
	return '% urbanized population: ' + str(country['data']['people']['urbanization']['urban_population']['value'])

def f_exports(master, country_name):
	country = master[country_name]['fb']
	d = country['data']['economy']['exports']
	s = 'chief exports: ' + ', '.join(d['commodities']['by_commodity'])
	s = s + '; major partners: '
	s = s + ', '.join(['{} {}%'.format(p['name'], p['percent']) for p in d['partners']['by_country']])
	return s

FACT_FUNCS = [f_current_environmental_issues, f_intl_environmental_agreements,
 f_climate, f_hazards, f_urban_population, f_exports]

def q_misc_facts(master, country_name):
	country = master[country_name]['fb']
	facts = FACT_FUNCS[:]
	random.shuffle(facts)
	facts = facts[0:random.randint(2, 3)]

	q = 'Facts:\n'
	for fact in facts:
		q = q + '- ' + fact(master, country_name) + '\n'
	return Question(message=q, answer=names(master, country_name))


def q_national_symbol(master, country_name):
	country_names = names(master, country_name)
	country = master[country_name]['fb']
	q = "This country's national symbol has"
	nat_sym = country['data']['government']['national_symbol']
	colors = None
	if 'colors' in nat_sym:
		colors = [c['color'] for c in nat_sym['colors']]
	syms = None
	if 'symbols' in nat_sym:
		syms = [s['symbol'] for s in nat_sym['symbols']]
	if colors is not None:
		q += ' the colors ' + ', '.join(colors)
		if syms is not None:
			q += ' and ' + ', '.join(syms)
		return Question(message=q, answer=country_names)
	if colors is None and syms is not None:
		return Question(message=q + ' the symbols ' + ', '.join(syms), answer=country_names)
	raise Exception('failed')

def q_capital_etymology(master, country_name):
	country = master[country_name]['fb']
	q = "Etymology of this counry's capital: "
	etymology = country['data']['government']['capital']['etymology']
	return Question(message=q + etymology, answer=names(master, country_name))

def q_country_name_etymology(master, country_name):
	country = master[country_name]['fb']
	q = "Etymology of this country's name: " + country['data']['government']['country_name']['etymology']
	return Question(message=q, answer=names(master, country_name))

def q_flag_image(master, country_name):
	if extract_country(master, country_name, 'out.png'):
		return Question(answer=names(master, country_name), image_path='out.png')
	raise Exception('No flag!')

def q_coat_of_arms(master, country_name):
	a = names(master, country_name)
	image = download_wikidata_svg(master, country_name, 'coatOfArms')
	return Question(answer=a, image_path=image)

def q_locator_map(master, country_name):
	a = names(master, country_name)
	image = dl_svg_as_png(random.choice(master[country_name]['wd']['mapImage']))
	return Question(answer=a, image_path=image)	

QUESTION_FUNCS = [q_intro_question, q_major_urban_areas, 
	q_linguistic_makeup, q_location, q_flag_description,
	q_national_symbol, q_capital_etymology, q_country_name_etymology, 
	q_misc_facts, q_flag_image, q_coat_of_arms, q_locator_map]

def all_questions_for_country(master, country):
	questions = {}
	for q in QUESTION_FUNCS:
		try:
			questions[q] = q(master, country)
		except:
			questions[q] = None
	return questions

def random_question_for_country(master, country_name):
	return random.choice(QUESTION_FUNCS)(country)

def random_country(master):
	return random.choice(list(master.keys()))

def random_question(master):
	possible_questions = QUESTION_FUNCS.copy()
	country = random_country(master)
	while len(possible_questions) > 0:
		selected_question = random.choice(possible_questions)
		possible_questions.remove(selected_question)
		try:
			sq = selected_question(master, country)
			assert type(sq) == Question
			return sq
		except Exception as e:
			print('Failed to use question {} for country {} with exception {}'.format(selected_question, master[country]['fb']['data']['name'], e))
	return 'FAILED TO GENERATE QUESTION FOR ' + country, country

def get_tld_country_code(master, country_name):
	try:
		return (master[country_name]['fb']['data']['communications']['internet']['country_code'][1:])[:2]
	except KeyError:
		return None

# uses a flags.zip from https://flagpedia.net/download , size doesn't matter as long as PNG
def extract_country(master, country_name, target_filename):
	code = get_tld_country_code(master, country_name)
	if code is None:
		return False
	fname = code + '.png'
	zf = zipfile.ZipFile('flags.zip')
	try:
		zf.extract(fname)
	except KeyError:
		return False
	os.rename(fname, target_filename)
	return True

if __name__ == '__main__':
	master = get_master()
	while True:
		rq = random_question(master)
		q = rq.message
		a = rq.answer
		img = rq.image_path
		print(bcolors.BOLD, q, bcolors.ENDC)
		if img is not None:
			print(bcolors.BOLD, img, bcolors.ENDC)
		resp = input()
		correct = resp.lower() == a.lower()
		print(correct)
		if not correct:
			print('Answer:', a)
