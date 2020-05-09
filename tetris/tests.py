import pickle, tetris
print('Testing soft drop')
g = tetris.TetrisState()
g.random_moves(40)
g.to_image('0.png')
g.soft_drop()
g.to_image('1.png')

print('Doing some simulations :)')
print(' Will create a ton of random boards, ensuring stone y is correct')

gameover_c = 0
for i in range(1000):
	g = tetris.TetrisState()
	g.random_moves(20)
	g.soft_drop()
	if not g.gameover and g.stone_y != 0:
		print('After a soft drop, new stone should be at y=0')
		print('Writing to pickle 0.pickle')
		pickle.dump(g, open('0.pickle', 'wb'))
		sys.exit(1)
	if g.gameover:
		gameover_c += 1
print('Gameovers generated: ' + str(gameover_c) + ' out of 1000')
