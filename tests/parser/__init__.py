from logger.levels import *

def run():
	important("running tokenizer tests")
	import tests.parser.tokenizertest
	tests.parser.tokenizertest.run()
	important("running parser tests")
	import tests.parser.parsertest
	tests.parser.parsertest.run()
