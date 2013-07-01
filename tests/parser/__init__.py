from logger.levels import *

def run():
	important("running tokenizer tests")
	import tests.parser.tokenizer
	tests.parser.tokenizer.run()
	important("running parser tests")
	import tests.parser.parser
	tests.parser.parser.run()
