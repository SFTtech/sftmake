from time import time
from sys import stdout
from util import inf, ttywidth, printedlen, ansicolorstring

class LogMessage:
	"""
	Contains data about one log message, such as the message text and arbitrary metadata fields
	"""
	def __init__(self, msg, **kw):
		"""
		msg
			Message text
		kw
			Arbitrary metadata fields
		"""
		self.msg = msg
		self.__dict__.update(kw)

	def __repr__(self):
		return "LogMessage(" + ", ".join((k + " = " + repr(self.__dict__[k]) for k in self.__dict__)) + ")"

class Logger:
	"""
	Thread-safe logger
	You are not supposed to instantiate this class; in fact, it is a class mainly for the lack of namespaces.
	"""
	def __init__(self):
		"""
		Starts the logger thread and schedules it for deletion on program exit
		"""
		from threading import Thread
		from queue import Queue
		import atexit
		self.actionqueue = Queue()
		self.inittime = time()
		self.sinks = []
		self.thread = Thread(target = self.__loop, name = "LoggerThread")
		self.thread.daemon = True
		self.running = True
		atexit.register(self.__stop)
		self.thread.start()

	def __loop(self):
		"""
		Main loop of the logger thread; simply executes any and all functions on the action queue
		"""
		while self.running:
			self.actionqueue.get()()

	def __stop(self):
		"""
		Stops the logger thread; called at program exit
		"""
		def action():
			self.running = False
		self.actionqueue.put(action)
		self.thread.join()

	def _log(self, msg):
		"""
		Logs a message
		Should not be called directly, but instead by calling LogLevel objects

		msg
			LogMessage object
		"""
		def action():
			for sink, logfilter in self.sinks:
				if logfilter(msg):
					sink.log(msg)
		self.actionqueue.put(action)

	def addsink(self, sink, logfilter = lambda msg: True):
		"""
		Adds a new LogSink, with an appropriate filter

		sink
			A LogSink object, or, really, any object that has a 'log' member method that accepts
			LogMessage objects
		logfilter
			A filter function, which is passed the LogMessage object and expected to return a boolean value,
			True indicating that the message should be redirected to the sink.
			You will probably want to simply use a 'lambda msg: msg.lvl >= message',
			but you may as well consider other criteria, such as the source file or thread name.
		"""
		def action():
			self.sinks.append((sink, logfilter))
		self.actionqueue.put(action)

#the Logger instantiation
logger = Logger()

class LogLevel():
	"""
	Represents a log level
	"""
	def __init__(self, numeric, shortname, colid):
		"""
		numeric
			Numeric value of the log level; more important log levels have higher values
		shortname
			3-letter abbreviation of the loglevel
		colid
			ANSI color id
		"""
		self.numeric = numeric
		self.shortname = shortname
		self.colid = colid

	#these methods are for comparision with other loglevels
	def __gt__(self, other):
		return self.numeric > other.numeric

	def __ge__(self, other):
		return self.numeric >= other.numeric

	def __lt__(self, other):
		return self.numeric < other.numeric

	def __le__(self, other):
		return self.numeric <= other.numeric

	def __call__(self, msg, data = None):
		"""
		Logs a message with this level

		msg
			Message text (string)
		data
			Auxilliary additional data
		"""
		from inspect import stack
		from threading import current_thread
		caller = stack()[1]
		logmsg = LogMessage(str(msg),
			t = time() - logger.inittime,
			lvl = self,
			lvlshortname = self.shortname,
			lvlcol = ansicolorstring(self.colid),
			nocol = ansicolorstring(''),
			callerfile = caller[1],
			callerfun = caller[3],
			callerline = caller[2],
			threadname = current_thread().name,
			data = data)
		logger._log(logmsg)

class LogSink:
	"""
	Abstract LogSink base class
	Accepts LogMessage objects with its 'log' member method
	"""
	def log(self, msg):
		raise NotImplementedError("Abstract base class 'LogSink' does not implement 'log'")

class LogStorage(LogSink):
	"""
	Log sink that simply stores all incoming messages in a list, for later manual evaluation
	"""
	def __init__(self, dumpatexit = None):
		"""
		dumpatexit
			If a filename is given, the list will be dumped there on exit, using pickle
		"""
		self.msgs = []
		if dumpatexit != None:
			import atexit
			atexit.register(self.__dump)
			self.dumpatexit = dumpatexit
		from threading import Lock
		self.mutex = Lock()

	def __dump(self):
		"""
		Dumps the message list to the filename specified in dumpatexit
		"""
		import pickle
		pickle.dump(self.msgs, open(self.dumpatexit, 'wb'))

	def get(self):
		"""
		returns
			A List of all log messages (as a copy), in a thread-safe manner
		"""
		with self.mutex:
			return [msg for msg in self.msgs]

	def log(self, msg):
		with self.mutex:
			self.msgs.append(msg)

class LogWriter(LogSink):
	"""
	Log sink that writes incoming messages to a file or terminal
	"""
	def __init__(self, logfile = stdout, fancy = True,
		leftfmt = "[{t:12.6f}] {lvlcol}{lvlshortname}{nocol} ",
		rightfmt = " [{threadname} {callerfile}:{callerline}]"):
		"""
		logfile
			The target logfile, as a writable python File
		fancy
			If True, and logfile is a terminal, try to write log output in a fancy way,
			with left and right info columns and auto-wrapped log messages in the center.
			Else, output is written in a traditional way, with the text of the left and right
			info columns simply preceeding the actual log message.
		leftfmt
			Format string for the left info column
		rightfmt
			Format string for the right info column
		"""
		self.logfile = logfile
		self.fancy = fancy
		self.leftfmt = leftfmt
		self.rightfmt = rightfmt

	def log(self, msg):
		#print the log message
		leftstr = self.leftfmt.format(**msg.__dict__)
		leftw = printedlen(leftstr)
		leftpadding = " " * leftw
		rightstr = self.rightfmt.format(**msg.__dict__)
		rightw = printedlen(rightstr)
		centerw = ttywidth(self.logfile) - leftw - rightw
		if centerw < 16 or centerw == inf or not self.fancy:
			#use traditional style
			self.logfile.write(leftstr.strip() + " " + rightstr.strip() + " " + msg.msg.strip() + '\n')
		else:
			#use fancy style
			lines = []
			for line in str(msg.msg).split('\n'):
				from textwrap import wrap
				wrappedline = wrap(line, centerw)
				if wrappedline == []:
					lines.append('')
				else:
					lines += wrappedline
			if lines == []:
				lines = ['']

			#print the first line, with leftstr and rightstr
			self.logfile.write(leftstr + lines[0].ljust(centerw) + rightstr + '\n')
			for line in lines[1:]:
				self.logfile.write(leftpadding + line + '\n')
