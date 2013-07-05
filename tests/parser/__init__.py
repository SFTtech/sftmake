from logger.levels import *
from logger.exceptions import handle_exceptions

def run():
	important("tests.parser.tokenizer.run()")
	import tests.parser.tokenizertest
	handle_exceptions(tests.parser.tokenizertest.run, sectionname = "tokenizer tests")
	important("tests.parser.parser.run()")
	import tests.parser.parsertest
	handle_exceptions(tests.parser.parsertest.run, sectionname = "parser tests")
