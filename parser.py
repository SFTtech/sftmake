#!/usr/bin/python3
import string

class ParserException(Exception):
	def __init__(self, pos, situation, expected, got):
		Exception.__init__(self, situation + ", expected " + expected + ", but got " + got)
		self.pos = pos
		self.situation = situation
		self.expected = expected
		self.got = got

def parse_statement(statement):
	import tokenizer
	tokens = tokenizer.tokenize_statement(statement)
	import wisentparser
	p = wisentparser.Parser()
	try:
		tree = p.parse(((token.tokentype.name, (token.text, token.pos)) for token in tokens))
	except p.ParseErrors as e:
		for token, expected in e.errors:
			found = repr(token[0])
			if len(expected) == 1:
				expected = expected[0]
			else:
				expected = "one of " + ", ".join()(repr(s) for s in expected)
			raise ParserException(0, "During parsing", expected, found)
	return tree
