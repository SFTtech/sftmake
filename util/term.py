import os, fcntl, termios, struct
from util.misc import inf

def ttywidth(f):
	"""
	Determines the width of a terminal

	f
		File object pointing to the terminal
	returns
		Width of the terminal, in characters, or +inf if the file does not represent a terminal or an other
		error has occured
	"""
	try:
		_, w, _, _ = struct.unpack('HHHH',
			fcntl.ioctl(f.fileno(), termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0)))
		return w
	except:
		return inf

def printedlen(s):
	"""
	Determines the length of a string excluding ANSI escape sequences such as color codes
	Does NOT consider tab characters, newlines etc, just ANSI escape sequences.

	returns
		Length of s, in characters
	"""
	result = 0
	escaped = False
	for c in s:
		if c == "\x1b" and not escaped:
			escaped = True
		if not escaped:
			result += 1
		elif c.isalpha() and escaped:
			escaped = False
	return result

def ansicolorstring(colid):
	"""
	Determines the ANSI escape sequence for a certain color code

	colid
		Color code, or any ';'-separated concatenation thereof
	returns
		ANSI escape sequence for colid
	"""
	return '\x1b[' + colid + 'm'

def interact(globs, banner = None):
	"""
	launch an interactive python console

	globs
		the global variable dict
	banner
		the banner string that is printed
	"""

	#try to read the user's .pyrc file
	try:
		import os
		exec(open(os.environ["PYTHONSTARTUP"]).read(), globs)
	except:
		pass

	def printdocstrings(obj):
		import inspect
		doc = inspect.getdoc(obj)
		if doc == None:
			print("No documentation available")
		else:
			print(doc)

	def printsourcecode(obj):
		import inspect
		src = inspect.getsource(obj)
		if src == None:
			print("No source code available")
		else:
			print(src)

	globs["printdocstrings"] = printdocstrings
	globs["printsourcecode"] = printsourcecode

	#activate tab completion
	import rlcompleter, readline, code
	readline.parse_and_bind("tab: complete")

	class NoHiddenMemberRLCompleter(rlcompleter.Completer):
		def attr_matches(self, text):
			matches = super().attr_matches(text)
			if text.split('.')[-1:][0].startswith("_"):
				#if the user wants to see hidden members, show them all
				return matches
			else:
				#else, filter them
				return [m for m in matches if m[len(text):len(text) + 1] != '_']

	readline.set_completer(NoHiddenMemberRLCompleter(globs).complete)

	class HelpfulInteractiveConsole(code.InteractiveConsole):
		""""
		Wrapper that will detect trailing '?' characters and try to print docstrings
		"""
		def runsource(self, source, filename="<input>", symbol="single"):
			if len(source) > 2 and source[-2:] in ["??", "(?"]:
				#try to display sourcecode
				super().runsource("printsourcecode(" + source[:-2] + ")", filename, symbol)
			elif len(source) > 1 and source[-1:] in '?(':
				#try to display help stuff
				super().runsource("printdocstrings(" + source[:-1] + ")", filename, symbol)
				return False
			else:
				#simply call the super method
				return super().runsource(source, filename, symbol)

	#launch session
	HelpfulInteractiveConsole(globs).interact(banner)
