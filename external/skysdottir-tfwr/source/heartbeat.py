def gen_heartbeat_path(path_ids):
	Z = get_world_size()
	count = 0
	
	for X in range(0, Z, 2):
		for Y in range(Z/2,Z):
			count += 1
			dir = North
			if (Y == Z-1):
				dir = East
			path_ids[(X,Y)] = (count, dir)
		
		for Y in range(Z-1, Z/2-1, -1):
			count += 1
			dir = South
			if (Y == Z/2 and X != Z-2):
				dir = East
			path_ids[(X+1, Y)] = (count, dir)
			
	for X in range(Z-1, -1, -2):
		for Y in range(Z/2-1,-1,-1):
			count += 1
			dir = South
			if (Y == 0):
				dir = West
			path_ids[(X,Y)] = (count, dir)
		
		for Y in range(0, Z/2, 1):
			count += 1
			dir = North
			if (Y == Z/2-1 and X != 1):
				dir = West
			path_ids[(X-1, Y)] = (count, dir)