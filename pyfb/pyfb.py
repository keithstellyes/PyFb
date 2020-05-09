import facebook

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
			allow_sphereical_photo=True)

	def get_post_reactions(self, post_id):
		return [r for r in self.graph.get_all_connections(id=post_id, connection_name='reactions')]

	def get_post_reaction_tally(self, post_id):
		reactions = self.get_post_reactions(post_id); print(reactions);
		tally = {}
		for reaction in reactions:
			if 'type' not in reaction.keys():
				continue # special reacts don't have a type!!!!!!
			if reaction['type'] not in tally.keys():
				tally[reaction['type']] = 0
			tally[reaction['type']] += 1
		return tally
	def comment_on_post(self, post_id, message):
		return self.graph.put_comment(object_id=post_id, message=message)

	def get_username_for_user_id(self, user_id):
		return self.graph.request('/{}?fields=name'.format(user_id))['name']