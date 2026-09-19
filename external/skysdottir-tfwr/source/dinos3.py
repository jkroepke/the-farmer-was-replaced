set_world_size(16)

import pos
import m_utils
import queue_utils
import heartbeat
import skyscraper
import hilbert
import starburst

path_ids = {}
current_cycle_length = 0
full_cycle_length = get_world_size()**2
current_tail_length = 1
next_apple = (0,0)


def prep_fn(x, y):
	harvest()
	if(get_ground_type() != Grounds.Soil):
		till()

def prep():
	change_hat(Hats.Sunflower_Hat)
	pos.goto(0,0)
	pos.traverse(prep_fn)
	m_utils.await()
	pos.goto(0,0)
	hilbert.gen_hilbert_path(path_ids)
	
def scoot(dir, sc):
	global current_tail_length
	global current_cycle_length
	global next_apple
	
	move(dir)
	here = (get_pos_x(), get_pos_y())
	current_cycle_length -= sc
	queue_utils.tpush((here, sc))
	
	if(here == next_apple):
		current_tail_length += 1
		next_apple = measure()
		return True
	else:
		tail = queue_utils.tpop()
		current_cycle_length += tail[1]
		return False

def get_tgt(here, dir):
	if dir == North:
		return (here[0],here[1]+1)
	if dir == East:
		return (here[0]+1, here[1])
	if dir == South:
		return (here[0],here[1]-1)
	if dir == West:
		return (here[0]-1,here[1])
	return here

def mod_between(tgt, start, end, mod):
	if(end < start):
		end += mod
	if(tgt < start):
		tgt += mod
	return (tgt >= start and tgt <= end)

def can_shortcut(here, dir):	
	global current_cycle_length
	global current_tail_length
	global full_cycle_length
	if not can_move(dir):
		return 0
	
	rand = random()
	tgt = (1-(current_tail_length*2/full_cycle_length))**1
	
	# simulated annealing, as we get longer trend towards the hamiltonian
	if(rand > tgt):
		return 0
	
	# Don't get ahead of my tail
	tail = queue_utils.tpeek()
	tail_loc = tail[0]
	
	tgt = get_tgt(here, dir)
	
	# Don't get ahead of my tail
	if(mod_between(path_ids[tgt][0],path_ids[tail_loc][0],path_ids[here][0],full_cycle_length)):
		return 0
	
	# Don't skip past the apple
	if(not mod_between(path_ids[tgt][0],path_ids[here][0],path_ids[next_apple][0],full_cycle_length)):
		return 0
	
	here_idx = path_ids[here][0]
	tgt_idx = path_ids[tgt][0]
	if(tgt_idx < here_idx):
		tgt_idx += full_cycle_length
	# less 1 because moving from n -> n+1 shortens the len by 0, not 1
	removed_len = tgt_idx - here_idx - 1
	
	# arbitrary +1 in case of apples on the return path
	if current_cycle_length - removed_len > current_tail_length + 1:
		# We can take this shortcut!
		return removed_len
	else:
		# Can't take this shortcut, gotta stay on the Hamiltonian path
		return 0

def dino_iter():
	global current_tail_length
	global full_cycle_length
	
	here = (get_pos_x(), get_pos_y())
	go_dir = path_ids[here][1]
	go_saves = 0
	
	# If we're covering more than half the board, just follow the Hamiltonian path
	if (current_tail_length >= full_cycle_length/2):
		return scoot(go_dir, go_saves)
	
	# Otherwise, allow shortcutting
	fave_dir = None
	wanna_dirs = []
	Z = get_world_size()
	
	# tuning option: Allow all shortcuts, or only those that get us closer to the apple?
	# Allowing all tends to lead to tail-chasing behavior sooner, as the greedy algorithm takes more shortcuts
	# But it's happier on the heartbeat and skyscraper paths
	# where the optimal path is often going away from the apple to get to the return path
	if False:
		wanna_dirs = [North, West, South, East]
	else:
		if(here[0] > next_apple[0]):
			wanna_dirs.append(West)
		if(here[0] < next_apple[0]):
			wanna_dirs.append(East)
		if(here[1] > next_apple[1]):
			wanna_dirs.append(South)
		if(here[1] < next_apple[1]):
			wanna_dirs.append(North)
	
	# small optimization for the heartbeat map:
	#if (here[1] > Z/2 and (next_apple[1] < Z/2 or next_apple[0] < here[0])):
		# try to get down to the fastlane
		#fave_dir = South
	
	#if (here[1] < Z/2-1 and (next_apple[1] >= Z/2 or next_apple[0] > here[0])):
		#fave_dir = North
	
	# optimization for the skyscraper map:
	#if (here[1] > 1 and next_apple[0] < here[0]):
		#fave_dir = South
	
	if (not go_dir == fave_dir):
		for dir in wanna_dirs:
			this_saves = can_shortcut(here, dir)
			if (this_saves > go_saves):
				go_dir = dir
				go_saves = this_saves
				break
	
	return scoot(go_dir, go_saves)

def dino_goto():
	while(not dino_iter()):
		continue

def farm():
	global full_cycle_length
	global current_tail_length
	global current_cycle_length
	global next_apple
	queue_utils.reset()
	pos.goto(0,0)
	change_hat(Hats.Dinosaur_Hat)
	
	current_tail_length = 1
	current_cycle_length = full_cycle_length
	next_apple = measure()
	queue_utils.tpush(((0,0),0))
	
	start = get_time()
	
	while (current_tail_length < full_cycle_length-1):
		dino_goto()
		
	# and freeze until 3:45
	while (get_time() - start < 225 ):
		continue
	
	change_hat(Hats.Sunflower_Hat)

def mow_fn(x, y):
	harvest()
	if(get_ground_type() != Grounds.Grassland):
		till()
		
def lawnmow():
	starburst.gen_starburst_path(path_ids)
	pos.traverse(mow_fn)
	m_utils.await()

	pos.goto(0,0)
	for i in range(get_world_size()**2):
		here = (get_pos_x(), get_pos_y())
		till()
		move(path_ids[here][1])
		
prep()
farm()