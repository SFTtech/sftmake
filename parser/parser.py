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
	from parser.tokenizer import tokenize_statement
	from parser.wisentparser import Parser

	tokens = ((t.tokentype.name, (t.text, t.pos)) for t in tokenize_statement(statement))
	p = Parser()
	try:
		tree = p.parse(tokens)
	except p.ParseErrors as e:
		for token, expected in e.errors:
			found = repr(token[0])
			if len(expected) == 1:
				expected = expected[0]
			else:
				expected = "one of " + ", ".join()(repr(s) for s in expected)
			raise ParserException(0, "During parsing", expected, found)
	return tree
