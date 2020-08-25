import facebook, os, sqlite3

is_user_cache = sqlite3.connect(os.path.dirname(os.path.abspath(__file__)) + '/is-user-cache.db')
is_user_cache.cursor().execute('CREATE TABLE IF NOT EXISTS IsUserCache(id TEXT, isUser INTEGER)')

def get_user_id(graph, access_token):
	r = graph.request('/me?fields=id&access_token="{}"'.format(access_token))
	return r['id']

class PyFb:
	def __init__(self, access_token):
		self.access_token = access_token
		self.graph = facebook.GraphAPI(access_token=access_token)
		self.user_id = get_user_id(self.graph, self.access_token)
	def get_posts(self):
		return self.graph.get_connections(id=self.user_id, connection_name='posts')

	def get_posts_date_descending(self):
		return self.get_posts() #todo

	def get_post_comments(self, post_id):
		return self.graph.get_all_connections(id=post_id, connection_name='comments')

	def create_post(self, message, image_path=None):
		if image_path is None:
			return self.graph.put_object(parent_object=self.user_id, message=message,
				connection_name='feed')
		else:
			return self.graph.put_photo(image=open(image_path, 'rb'), message=message)

	def create_360_photo_post(self, message, image_path):
		return self.graph.put_photo(image=open(image_path, 'rb'), message=message, 
			allow_spherical_photo=True)

	def get_post_reactions(self, post_id):
		return [r for r in self.graph.get_all_connections(id=post_id, connection_name='reactions')]

	def get_post_reaction_tally(self, post_id):
		reactions = self.get_post_reactions(post_id); print(reactions);
		tally = {}
		users = []
		not_users = []
		for reaction in reactions:
			if 'type' not in reaction.keys():
				continue # special reacts don't have a type!!!!!!
			if not(self.is_user(reaction['id'])):
				not_users.append(reaction)
				continue
			else:
				users.append(reaction)
			if reaction['type'] not in tally.keys():
				tally[reaction['type']] = 0
			tally[reaction['type']] += 1
		print('users:{} not users: {}'.format(users, not_users))
		return tally
	def comment_on_post(self, post_id, message):
		return self.graph.put_comment(object_id=post_id, message=message)

	def get_username_for_user_id(self, user_id):
		return self.graph.request('/{}?fields=name'.format(user_id))['name']

	# Facebook makes this more painful than it really should be to check
	def is_user(self, id):
		result = True
		cursor = is_user_cache.cursor()
		cursor.execute('SELECT isUser FROM IsUserCache WHERE id = ? LIMIT 1', (id,))
		results = cursor.fetchall()
		if len(results) > 0:
			print('Cache hit for {}, results: {}, {}'.format(id, results, results[0][0] == 1))
			return results[0][0] == 1
		try:
			result = self.graph.request('/{}?metadata=1'.format(id))['metadata']['type'] == 'user'
		except facebook.GraphAPIError as e:
			# #10 is returned on no permissions, we don't have permission to read pages
			# of course, 500 errors are possible too, so we 
			result = not(str(e).startswith('(#10)'))
		print('cache miss for {} got {}'.format(id, result))
		resulti = result == 1
		cursor.execute('INSERT INTO IsUserCache(isUser, id) VALUES(?, ?)', (resulti, id))
		is_user_cache.commit()
		return result