def get_key_path(obj, key, pre_path=[]):
	try:
		obj.keys()
	except AttributeError:
		return None
	if key in obj.keys():
		return pre_path + [key]
	paths = []
	for potential_ancestor in obj.keys():
		path = get_key_path(obj[potential_ancestor], key=key, pre_path=pre_path+[potential_ancestor])
		if path is not None:
			paths.append(path)
	if paths == []:
		return None
	return paths

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

def normalize_answer(ans):
	ans = ans.lower()
	if ans.count(',') == 1:
		post, pre = ans.split(',')
		ans = pre + post
	ans = ans.replace('the', '')
	ans = ans.replace(' ', '').replace(',','').replace('!','').replace('?','')
	ans = ans.replace('whatis','').replace('whereis','')
	return ans

def accept_answer(actual, possible_answers, tolerance=3):
	possible_types_for_possible_answers = (list, set, tuple)
	assert type(possible_answers) in possible_types_for_possible_answers
	actual = normalize_answer(actual)

	for expect in possible_answers:
		expect = normalize_answer(expect)
		if len(actual) <= 3:
			if expect == actual:
				return True
		else:
			if minimumEditDistance(expect, actual) <= tolerance:
				return True
	return False