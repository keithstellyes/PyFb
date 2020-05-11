import json, requests, string

def get_questions(count):
	if type(count) != int:
		raise Exception('Count must be an int')
	if count < 1 or count > 100:
		raise Exception('Count must be 1 <= n <= 100')
	r = requests.get('http://jservice.io/api/random?count={}'.format(count))
	if r.status_code != 200:
		raise Exception('Issue getting questions. Expected status code 200: ' + str(r))
	return json.loads(r.text)

def get_questions_succinct(count):
	questions = get_questions(count)
	results =[]
	for q in questions:
		results.append({'id':q['id'], 'question':q['question'], 
			'answer':q['answer'], 'category':q['category']['title'].title(),
			'json':json.dumps(q)})
	return results


def answer_clean(s):
	s = s.replace('<i>', '')
	s = s.replace('</i>', '')
	for c in string.punctuation:
		s = s.replace(c, '')
	for c in string.whitespace:
		s = s.replace(c, '')
	s = s.upper()
	s = s.replace('WHATIS', '')
	s = s.replace('WHOIS', '')
	return s

if __name__ == '__main__':
	questions = get_questions_succinct(10)
	for q in questions:
		print('ID:', q['id'])
		print('Category:', q['category'])
		print('Question:', q['question'])
		print('Answer:', q['answer'])
		print('=====================')