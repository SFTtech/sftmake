from logger.levels import *

def run():
	important("running parser tests")
	import tests.parser
	tests.parser.run()

