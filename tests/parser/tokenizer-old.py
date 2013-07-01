#!/usr/bin/python3
import tokenizer
from testing import *

def tokenizer_testfun(test):
	(testline, expected) = test
	if type(expected) == tuple:
		#we want the tokenizer to throw an exception
		expected, expected_position = expected
		try:
			tokens = tokenizer.tokenize_line(testline)
		except Exception as e:
			try:
				positionstring = " at position " + str(e.pos)
			except:
				positionstring = ""

			if type(e) != expected or e.pos != expected_position:
				redprint("Expected tokenizer to raise exception " + expected.__name__ + " at position " + str(expected_position) + ", but got exception " +
						type(e).__name__ + positionstring + ", text: " + str(e))
			else:
				return True
		else:
			redprint("Expected tokenizer to raise exception " + expected.__name__ + " at position " + str(expected_position) + ", but got token list:")
			print(list(map(lambda t: (t[0], t[1][0]), tokens[i:])))

	elif type(expected) == list:
		#we want the tokenizer to generate a token list
		expected_tokens = []
		#for better usability, tokens may be encoded (special tokens such as (";", ";") and (",", ",") may be represented as a string ";,".
		#decode that.
		for expected_token in expected:
			if type(expected_token) == tuple:
				expected_tokens.append(expected_token)
			elif type(expected_token) == str:
				for c in expected_token:
					expected_tokens.append((str(c),str(c)))
			else:
				redprint("Test invalid: Invalid expected token specification: " + str(expected_token))
				return False

		#invoke the tokenizer
		try:
			tokens = tokenizer.tokenize_line(testline)
		except Exception as e:
			redprint("Got exception of type " + type(e).__name__ + ", text: " + str(e))
			cyanprint("Expected token list:")
			print(expected_tokens)

		#parse the results of the tokenizer
		all_valid = True
		invalid_count = 0
		expected_str = returned_str = ""
		for i, (name, (content, pos)) in enumerate(tokens):
			token = (name, content)
			try:
				expected = expected_tokens[i]
			except IndexError:
				redprint("Expected end of token list, but tokenizer returned additional tokens")
				cyanprint("Tokens so far:")
				print(expected_str)
				cyanprint("Additional tokens:")
				print(list(map(lambda t: (t[0], t[1][0]), tokens[i:])))
				return False

			if i != 0:
				expected_str += ", "
				returned_str += ", "

			if token != expected:
				all_valid = False
				invalid_count += 1
				expected_str += colcode(31)
				returned_str += colcode(31)

			expected_str += str(expected) + colcode()
			returned_str += str(token) + colcode()

		if len(tokens) < len(expected_tokens):
			redprint("Additional tokens expected: " + str(len(expected_tokens) - len(tokens)))
			all_valid = False
			expected_str += colcode(33)
			for expected in expected_tokens[len(tokens):]:
				expected_str += ", " + str(expected)
			expected_str += colcode()

		if not all_valid:
			if invalid_count > 0:
				redprint("Invalid tokens: " + str(invalid_count))
			cyanprint("Expected tokens:")
			print(expected_str)
			cyanprint("Tokenizer returned:")
			print(returned_str)
		else:
			return True
	else:
		redprint("Test line invalid: 'expected' is neither a tuple, nor a list")
	return False

if not testseries("Tokenizer", tokenizer_testfun, lambda t: "'" + t[0] + "'",
	("var=value", [
			("IDENTIFIER", "var"), "=",
			("IDENTIFIER", "value")]),

	("var[cond=val]=val42ue", [
			("IDENTIFIER", "var"), "[",
			("IDENTIFIER", "cond"), "=",
			("IDENTIFIER", "val"), "]=",
			("IDENTIFIER", "val42ue")]),

	("", [
			]),

	("a0 0a _a _0 _ä _\\  _\\\\ _\\[ _\\x61 _\\xAC _\\xac _\\u0061\t", [
			("IDENTIFIER", "a0"), ("WHITESPACE", " "),
			("LITERAL",    "0a"), ("WHITESPACE", " "),
			("IDENTIFIER", "_a"), ("WHITESPACE", " "),
			("IDENTIFIER", "_0"), ("WHITESPACE", " "),
			("LITERAL",    "_ä"), ("WHITESPACE", " "),
			("LITERAL",    "_ "), ("WHITESPACE", " "),
			("LITERAL",    "_\\"), ("WHITESPACE", " "),
			("LITERAL",    "_["), ("WHITESPACE", " "),
			("LITERAL",    "_a"), ("WHITESPACE", " "),
			("LITERAL",    "_\xac"), ("WHITESPACE", " "),
			("LITERAL",    "_\xac"), ("WHITESPACE", " "),
			("LITERAL",    "_a"), ("WHITESPACE", "\t")]),

	("var[x=$(fun arg     \"  \" ' '  \" \" ' \" \"')]+=\\u262d", [
			("IDENTIFIER", "var"), "[",
			("IDENTIFIER", "x"), "=$(",
			("IDENTIFIER", "fun"),
			("WHITESPACE", " "),
			("IDENTIFIER", "arg"),
			("WHITESPACE", "     "), '"',
			("WHITESPACE", "  "), '"',
			("WHITESPACE", " "), "'",
			("WHITESPACE", " "), "'",
			("WHITESPACE", "  "), '"',
			("WHITESPACE", " "), '"',
			("WHITESPACE", " "), "'",
			("WHITESPACE", " "), '"',
			("WHITESPACE", " "), "\"')]+=",
			("LITERAL", "\u262d")]),

	("a'b$'c\"a'b\"c'\"'", [
			("IDENTIFIER", "a"), "'",
			("IDENTIFIER", "b"), "$'",
			("IDENTIFIER", "c"), '"',
			("IDENTIFIER", "a"), "'",
			("IDENTIFIER", "b"), '"',
			("IDENTIFIER", "c"), "'\"'"]),

	("\\xHH", (tokenizer.TokenizerXEscapeIllegalCharacterException, 1))

	):
	exit(1)
