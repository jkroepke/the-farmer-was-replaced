queue = []
max_q = 1024
head_ptr = 0
tail_ptr = 0

def reset():
	global max_q
	global head_ptr
	global tail_ptr
	
	queue = []
	Z = get_world_size()
	max_q = Z**2
	head_ptr = 0
	tail_ptr = 0


def tpush(item):
	global max_q
	global head_ptr
	if(queue.len() < max_q):
		queue.append(item)
		head_ptr += 1
		head_ptr %= max_q
	else:
		queue[head_ptr] = item
		head_ptr += 1
		head_ptr %= max_q

def tpop():
	global tail_ptr
	global max_q
	item = queue[tail_ptr]
	tail_ptr += 1
	tail_ptr %= max_q
	return item
	
def tpeek():
	global tail_ptr
	return queue[tail_ptr]