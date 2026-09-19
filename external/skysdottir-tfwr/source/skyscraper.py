def gen_skyscraper_path(path_ids):
	Z = get_world_size()

	count = 0
	
	path_ids[(0,0)] = (0, North)
	
	for X in range(0, Z, 2):
		for Y in range(1,Z):
			count += 1
			dir = North
			if (Y == Z-1):
				dir = East
			path_ids[(X,Y)] = (count, dir)
		
		for Y in range(Z-1, 0, -1):
			count += 1
			dir = South
			if (Y == 1 and X != Z-2):
				dir = East
			path_ids[(X+1, Y)] = (count, dir)
	
	for X in range(Z-1, 0, -1):
		count += 1
		path_ids[(X, 0)] = (count, West)