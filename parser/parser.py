import string
from logger.levels import *
from parser.wisentparser import Parser
from parser.tokenizer import tokenize_statement
from parser.exceptions import *

p = Parser()

def wisent_parsetree_to_string(tree, indent = 0):
	"""
	converts a wisent-generated parsetree to a human-readable string

	tree
		the parsetree
	indent
		for indentation management in recursive calls
	"""
	result = ""
	prefix = '\t' * indent
	if tree[0] in p.terminals:
		result += prefix + repr(tree) + '\n'
	else:
		result += prefix + repr(tree[0]) + '\n'
		for x in tree[1:]:
			result += wisent_parsetree_to_string(x, indent + 1) + '\n'

	return result[:-1]

def parse_statement(statement):
	tokens = (t.totuple() for t in tokenize_statement(statement))
	try:
		tree = p.parse(tokens)
	except p.ParseErrors as e:
		for token, expected in e.errors:
			raise ParserUnexpectedTokenException(token, expected) from None
			#for now, only the first error is reported

	return tree
