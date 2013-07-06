from logger.levels import *
from logger.exceptions import handle_exceptions

def run():
	important("tests.parser.run()")
	import tests.parser
	handle_exceptions(tests.parser.run, sectionname = "parser tests")

