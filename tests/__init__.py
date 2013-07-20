from logger.levels import *
from logger.exceptions import handle_exceptions

class test:

	def __init__(self, n, modname, funcname=None):
		self.name = n
		self.module_name = modname
		self.call = funcname

	def run(self):
		important("TESTING: " + self.name)
		exec("import " + self.module_name)
		if self.call != None:
			debug("call will be " + self.call)
			func = eval(self.call)
			debug("function = " + str(func))
			handle_exceptions(func, self.name)


def run(which=None):

	tests = []

	tests.append(test(
		n="util.path",
		modname="tests.abspath_subfolder",
		funcname="tests.abspath_subfolder.run"
	))

	tests.append(test(
		n="tests.builder.run",
		modname="tests.builder",
	))

	tests.append(test(
		n="tests.parser.run",
		modname="tests.parser",
		funcname="tests.parser.run"
	))

	for t in tests:
		if which != None and t.name in which:
			t.run()
