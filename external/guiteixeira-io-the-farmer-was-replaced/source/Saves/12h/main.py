change_hat(Hats.Purple_Hat)
do_a_flip()
while True:
	if can_harvest():
		harvest()
	else:
		do_a_flip()

