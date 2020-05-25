import json, os, random, sqlite3, zipfile

this_dir = os.path.dirname(os.path.abspath(__file__))
FACTBOOK_PATH = this_dir + '/factbook.json'

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

def get_factbook():
	return json.load(open(FACTBOOK_PATH, 'r'))

def q_intro_question(country):
	sents = country['data']['introduction']['background'].split('\n')[0].split('.')
	segment_begin_max = len(sents) - 2
	segment_begin = random.randint(0, segment_begin_max)
	intro = '.'.join(sents[segment_begin:(segment_begin + 2)])

	return intro.replace(country['data']['name'], '[COUNTRY]'), country['data']['name']

def q_major_urban_areas(country):
	q = "The major urban areas of this country include: "
	urban_areas = [ua['place'] for ua in country['data']['people']['major_urban_areas']['places']]
	if len(urban_areas) == 1:
		return "The major urban area of this country is " + urban_areas[0], country['data']['name']
	q += ', '.join(urban_areas[:-1])
	q += ' and ' + urban_areas[-1]
	return q, country['data']['name']

def q_linguistic_makeup(country):
	q = "The linguistic makeup of this country is: "
	langs = []
	for lang in country['data']['people']['languages']['language']:
		lang_full = lang['name']
		if 'note' in lang.keys():
			lang_full += '({})'.format(lang['note'])
		langs.append(lang_full)
	q += ', '.join(langs)
	return q, country['data']['name']

def q_location(country):
	q = "This country is in " + country['data']['geography']['location']
	return q, country['data']['name']

def q_flag_description(country):
	q = "This country's flag "
	fd = country['data']['government']['flag_description']
	q += fd['description']
	if 'note' in fd.keys():
		q += '; ' + fd['note']
	return q, country['data']['name']

# f_ fact
def f_current_environmental_issues(country):
	return 'environmental issues: ' + ','.join(country['data']['geography']['environment']['current_issues'])

def f_intl_environmental_agreements(country):
	s = 'party to the following international environmental agreements: ' 
	return s + ','.join(country['data']['geography']['environment']['international_agreements']['party_to'])

def f_climate(country):
	return 'climate: ' + country['data']['geography']['climate']

def f_hazards(country):
	return 'natural hazards: ' + ', '.join([h['description'] for h in country['data']['geography']['natural_hazards']])

def f_urban_population(country):
	return '% urbanized population: ' + str(country['data']['people']['urbanization']['urban_population']['value'])

def f_exports(country):
	d = country['data']['economy']['exports']
	s = 'chief exports: ' + ', '.join(d['commodities']['by_commodity'])
	s = s + '; major partners: '
	s = s + ', '.join(['{} {}%'.format(p['name'], p['percent']) for p in d['partners']['by_country']])
	return s

FACT_FUNCS = [f_current_environmental_issues, f_intl_environmental_agreements,
 f_climate, f_hazards, f_urban_population, f_exports]

def q_misc_facts(country):
	facts = FACT_FUNCS[:]
	random.shuffle(facts)
	facts = facts[0:random.randint(2, 3)]

	q = 'Facts:\n'
	for fact in facts:
		q = q + '- ' + fact(country) + '\n'
	return q, country['data']['name']


def q_national_symbol(country):
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
		return q, country['data']['name']
	if colors is None and syms is not None:
		return q + ' the symbols ' + ', '.join(syms), country['data']['name']
	raise Exception('failed')

def q_capital_etymology(country):
	q = "Etymology of this counry's capital: "
	etymology = country['data']['government']['capital']['etymology']
	return q + etymology, country['data']['name']

def q_country_name_etymology(country):
	q = "Etymology of this country's name: " + country['data']['government']['country_name']['etymology']
	return q, country['data']['name']


QUESTION_FUNCS = [q_intro_question, q_major_urban_areas, 
	q_linguistic_makeup, q_location, q_flag_description,
	q_national_symbol, q_capital_etymology, q_country_name_etymology]

def all_questions_for_country(country):
	questions = {}
	for q in QUESTION_FUNCS:
		try:
			questions[q] = q(country)
		except:
			questions[q] = None
	return questions

def random_question_for_country(country):
	return random.choice(QUESTION_FUNCS)(country)

def random_country(factbook):
	return factbook['countries'][random.choice(list(factbook['countries']))]

def random_question(factbook):
	possible_questions = QUESTION_FUNCS.copy()
	country = random_country(factbook)
	while len(possible_questions) > 0:
		selected_question = random.choice(possible_questions)
		possible_questions.remove(selected_question)
		try:
			return selected_question(country)
		except Exception as e:
			print('Failed to use question {} for country {} with exception {}'.format(selected_question, country['data']['name'], e))
	return 'FAILED TO GENERATE QUESTION FOR ' + country, country

def random_flag(factbook, target_filename='out-flag.png'):
	while True:
		country = random_country(factbook)
		if extract_country(factbook, country, target_filename):
			return country['data']['name']

# uses a flags.zip from https://flagpedia.net/download , size doesn't matter as long as PNG
def extract_country(factbook, country, target_filename):
	code = None
	try:
		code = country['data']['communications']['internet']['country_code']
	except KeyError:
		return False
	code = code[1:]
	fname = code + '.png'
	zf = zipfile.ZipFile('flags.zip')
	try:
		zf.extract(fname)
	except KeyError:
		return False
	os.rename(fname, target_filename)
	return True
if __name__ == '__main__':
	factbook = get_factbook()
	f = open('malaysia.json', 'w')
	json.dump(factbook['countries']['malaysia'], f, sort_keys=True, indent=4)
	f.close()

	while True:
		q, a = random_question(factbook)
		print(bcolors.BOLD, q, bcolors.ENDC)
		resp = input()
		correct = resp.lower() == a.lower()
		print(correct)
		if not correct:
			print('Answer:', a)