import random, sys, json
sys.path.insert(0, '..')
from pyfb.pyfb import PyFb
import imagedrawer, model

fb_client = PyFb(json.load(open('../tokens.json', 'r'))['exodia'])
deck = model.Deck(id=0)
hand = deck.draw_five()

image_path = 'out.png'
imagedrawer.draw_hand('bg.jpg', hand, out_path=image_path)
message = ''
if sorted(hand) == model.EXODIA_HAND:
	message = "THE UNSTOPPABLE EXODIA! I'VE ASSEMBLED ALL FIVE SPECIAL CARDS! ALL FIVE PIECES OF THE PUZZLE! EXODIA! OBLITERATE!!!\n"
message = message + '\n' + '\n'.join(hand)
print(message)
pid = fb_client.create_post(message=message, image_path=image_path)['post_id']
session = model.Session()
session.add(model.Post.from_fb_post_id_and_hand(pid, hand))
session.commit()