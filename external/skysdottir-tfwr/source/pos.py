def goto(X, Y):
	Z = get_world_size()
	cx = get_pos_x()
	cy = get_pos_y()
	
	if (cy < Y):
		cy += Z
	if (cx < X):
		cx += Z
		
	if (cy - Y > Z/2):
		while(get_pos_y() != Y):
			move(North)
	else:
		while(get_pos_y() != Y):
			move(South)
	
	if(cx - X > Z/2):
		while(get_pos_x() != X):
			move(East)
	else:
		while(get_pos_x() != X):
			move(West)
			
def gotot(tuple):
	goto(tuple[0], tuple[1])

def join(l1, l2):
	for e in l2:
		l1.append(e)
	return l1

def subdivide(x, y, dx, dy, D):
	if(D==1):
		return [(x, y, dx, dy)]
	if (dx - x > dy - y):
		# Splitting along the X axis
		half = ((dx - x) // 2) + x
		low = subdivide(half, y, dx, dy, D//2)
		high = subdivide(x, y, half, dy, D//2)
		return join(low, high)
	else:
		# Splitting along the Y axis
		half = ((dy - y) // 2) + y
		low2 = subdivide(x, half, dx, dy, D//2)
		high2 = subdivide(x, y, dx, half, D//2)
		return join(low2, high2)

def divide():
	Z = get_world_size()
	D = max_drones()
	
	zones = subdivide(0, 0, Z, Z, D)
	
	return zones

def subtraverse(sx, sy, dx, dy, fn):
	for x in range(sx, dx):
		goto(x, sy)
		for y in range(sy, dy):
			fn(x, y)
			move(North)

def df(f, arg):
	def g():
		f(arg)
	return g

def st(payload):
	zone = payload[0]
	fn = payload[1]
	subtraverse(zone[0], zone[1], zone[2], zone[3], fn)

def traverse(fn):
	for zone in divide():
		payload = (zone, fn)
		if (num_drones() < max_drones()):
			spawn_drone(df(st, payload))
		else:
			#last one, do it meself!
			st(payload)
			