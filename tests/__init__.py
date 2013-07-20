from logger.levels import *
from logger.exceptions import handle_exceptions

from tests.testing import coltext

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
			return func()

	def __repr__(self):
		return "test {" + self.name + "}"


def run(which=None):

	if which != None:
		message(coltext("TESTING IS THE FUTURE", 32))
		message(coltext("AND THE FUTURE STARTS WITH YOU!", 32))
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
		n="builder.run",
		modname="tests.builder",
		funcname="tests.builder.run"
	))

	tests.append(test(
		n="parser.run",
		modname="tests.parser",
		funcname="tests.parser.run"
	))

	availtestmsg = "[" + ", ".join(t.name for t in tests) + "]"
	message("available tests:\n" + availtestmsg)

	for t in tests:
		if which != None and t.name in which:
			ok = t.run()
			debug("test " + repr(t) + " was " + str(ok))
			if ok:
				success.append(t)

			else:
				fail.append(t)

	message("finished all tests")

	for t in success:
		important(coltext("SUCCESS:\t", 32) + repr(t))

	for t in fail:
		error(coltext("FAIL:\t", "1;31") + repr(t))
