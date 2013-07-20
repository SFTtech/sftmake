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

	def __repr__(self):
		return "test {" + self.name + "}"


def run(which=None):

	if which != None:
		message("TESTING IS THE FUTURE")
		message("AND THE FUTURE STARTS WITH YOU!")
		message("enabled tests:\n" + str(which))

	tests = []
	success = []
	fail = []

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
			if t.run():
				success.append(t)

			else:
				fail.append(t)

	message("finished all tests")

	for t in success:
		important("SUCCESS:" + repr(t))

	for t in fail:
		important("FAIL:" + repr(t))
