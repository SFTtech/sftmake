inf = float("+inf")
nan = float("NaN")

def get_thread_count():
	"""gets the number or hardware threads, or 1 if that can't be done"""

	import multiprocessing

	try:
		return multiprocessing.cpu_count()
	except NotImplementedError: # may happen under !POSIX
		fallback = 1
		sys.stderr.write('warning: cpu number detection failed, fallback to ' + fallback + '\n')
		return fallback

def concat(lists):
	for l in lists:
		for val in l:
			yield val
