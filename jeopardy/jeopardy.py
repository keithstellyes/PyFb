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

# stolen from Rosetta Code
def minimumEditDistance(s1,s2):
    if len(s1) > len(s2):
        s1,s2 = s2,s1
    distances = range(len(s1) + 1)
    for index2,char2 in enumerate(s2):
        newDistances = [index2+1]
        for index1,char1 in enumerate(s1):
            if char1 == char2:
                newDistances.append(distances[index1])
            else:
                newDistances.append(1 + min((distances[index1],
                                             distances[index1+1],
                                             newDistances[-1])))
        distances = newDistances
    return distances[-1]

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

def accept_answer(expect, actual, edit_threshold=3):
	return minimumEditDistance(answer_clean(expect), answer_clean(actual)) <= edit_threshold

if __name__ == '__main__':
	questions = get_questions_succinct(10)
	for q in questions:
		print('ID:', q['id'])
		print('Category:', q['category'])
		print('Question:', q['question'])
		print('Answer:', q['answer'])
		print('=====================')