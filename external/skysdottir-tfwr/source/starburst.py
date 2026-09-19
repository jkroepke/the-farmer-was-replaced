import pos
trace = False

opposite_dir = {
	North: South,
	South: North,
	East: West,
	West: East
}

def log_move(loc, dir):
	global trace
	if trace:
		move(dir)
		
	X = loc[0]
	Y = loc[1]
	
	if (dir == North):
		return (X, Y+1)
	if (dir == South):
		return (X, Y-1)
	if (dir == East):
		return (X+1, Y)
	if (dir == West):
		return (X-1, Y)
	
	return (X, Y)

def gen_ray_half(path_ids, here, side_dir, half_dir, ray_len, start_index):
	for i in range(ray_len):
		path_ids[here] = (start_index, half_dir)
		here = log_move(here, half_dir)
		start_index += 1
	
	path_ids[here] = (start_index, side_dir)
	here = log_move(here, side_dir)
	start_index += 1
	
	return (start_index, here)

# We're already on the first square of the ray - go out, up, back, up again to the start of the next ray
def gen_starburst_ray(path_ids, here, side_dir, ray_dir, ray_len, start_index):
	global trace
	if trace:
		print(start_index)
	
	start_index, here = gen_ray_half(path_ids, here, side_dir, ray_dir, ray_len, start_index)
	start_index, here = gen_ray_half(path_ids, here, side_dir, opposite_dir[ray_dir], ray_len, start_index)
	
	return (start_index, here)

# Don't generate the final square - not that it matters, but the next loop will take care of it
def gen_starburst_side(path_ids, here, side_dir, ray_dir, first_len, start_index, trim_longest_ray):
	Z = get_world_size()
	
	# first square
	path_ids[here] = (start_index, side_dir)
	here = log_move(here, side_dir)
	start_index += 1
		
	for i in range((Z-2)/4):
		trim = 0
		if (trim_longest_ray and (i+1)>=((Z-2)/4)):
			# last ray, reduce length by 1
			trim = 1
			
		start_index, here = gen_starburst_ray(path_ids, here, side_dir, ray_dir, (i*2) + first_len - trim, start_index)
		
	for i in range((Z-2)/4 - 1, 0, -1):
		start_index, here = gen_starburst_ray(path_ids, here, side_dir, ray_dir, i*2+first_len - 1, start_index)
		
	return start_index, here

def gen_starburst_path(path_ids):
	global trace
	Z = get_world_size()
	start_index = 0
	here = (0,0)
	
	if(trace):
		pos.gotot(here)
	
	start_index, here = gen_starburst_side(path_ids, here, North, East, 0, start_index, False)
	start_index, here = gen_starburst_side(path_ids, here, East, South, 2, start_index, True)
	start_index, here = gen_starburst_side(path_ids, here, South, West, 0, start_index, False)
	start_index, here = gen_starburst_side(path_ids, here, West, North, 2, start_index, True)
	
	