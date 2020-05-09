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