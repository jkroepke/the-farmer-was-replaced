# A note: the Hilbert curve generator only works on farms that are of size 2^n

dir_2_entry_corner = {
	East: (0, 1),
	West: (1, 0),
	South: (0, 1),
	North: (1, 0)
}

paths = {
(North, North): [West, North, East, North],
(South, South): [East, South, West, South],
(East, East): [South, East, North, East],
(West, West): [North, West, South, West],
(North, East): [West, North, East, East],
(North, West): [North, West, South, West],
(East, North): [South, East, North, North],
(East, South): [East, South, West, South],
(South, East): [South, East, North, East],
(South, West): [East, South, West, West],
(West, North): [West, North, East, North],
(West, South): [North, West, South, South] 
}

def hilbert_move(loc, delta, dir):
	X = loc[0]
	Y = loc[1]
	
	if (dir == North):
		return (X, Y+delta)
	if (dir == South):
		return (X, Y-delta)
	if (dir == East):
		return (X+delta, Y)
	if (dir == West):
		return (X-delta, Y)
	
	return (X, Y)

# All directions are directions of travel
# So, enter is the direction we're traveling when we enter the square
def hilbert_recurse(enter, exit, loc, delta, range_start, path_ids):
	# end condition!
	if (delta == 1):
		path_ids[loc] = (range_start, exit)
		return
	
	d = delta/2
	
	# Otherwise, recurse!
	path = paths[(enter, exit)]
	entry_corner = dir_2_entry_corner[enter]
	subsq = ((loc[0] + entry_corner[0]*d),(loc[1] + entry_corner[1]*d))
	e = enter
	for i in range(path.len()):
		dir = path[i]
		hilbert_recurse(e, dir, subsq, d, range_start+(i*d**2), path_ids)
		subsq = hilbert_move(subsq, d, dir)
		e = dir

def gen_hilbert_path(path_ids):
	d = get_world_size()/2
	
	here = (0,0)
	e = West
	path = [North, East, South, West]
	
	for i in range(4):
		dir = path[i]
		hilbert_recurse(e, dir, here, d, i * d**2, path_ids)
		here = hilbert_move(here, d, dir)
		e = dir