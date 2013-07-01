#!/usr/bin/python3
import string

class ParserException(Exception):
	def __init__(self, pos, situation, expected, got):
		Exception.__init__(self, "In " + situation + ", expected " + expected + ", but got " + got)
		self.pos = pos
		self.situation = situation
		self.expected = expected
		self.got = got

#all of these exception types are required for automatic testing
class TokenizerException(ParserException):
	pass
class TokenizerEscapeSequenceException(TokenizerException):
	pass
class TokenizerXEscapeIllegalCharacterException(TokenizerEscapeSequenceException):
	pass
class TokenizerXEscapeEndOfLineException(TokenizerEscapeSequenceException):
	pass
class TokenizerUEscapeIllegalCharacterException(TokenizerEscapeSequenceException):
	pass
class TokenizerUEscapeEndOfLineException(TokenizerEscapeSequenceException):
	pass
class TokenizerEscapeIllegalCharacterException(TokenizerEscapeSequenceException):
	pass
class TokenizerEscapeEndOfLineException(TokenizerEscapeSequenceException):
	pass

#TODO add testcases for all of these exceptions

#constants for tokenizer
CHAR_SPECIAL = EnumVal("special character")
CHAR_OTHER = EnumVal("miscellanious character")
CHAR_WS = EnumVal("Whitespace character")
CHAR_ALPHABETIC = EnumVal("Alphabetic character")
CHAR_DIGIT = EnumVal("Digit character")
CHAR_ENDOFSTATEMENT = EnumVal("End of statement (virtual character)")

ABSORB_WS_FORCED = EnumVal("Token is expects and absorbs a whitespace on this side")
ABSORB_WS = EnumVal("Token absorbs a whitespace on this side, if it exists")
NO_ABSORB_WS = EnumVal("Token does not absorb whitespaces on this side")

TOKEN_STARTOFSTATEMENT = EnumVal("Start of statement (virtual token)", tokenname = "STARTOFSTATEMENT")
TOKEN_ENDOFSTATEMENT = EnumVal("End of statement (virtual token)", tokenname = "ENDOFSTATEMENT")
TOKEN_WS = EnumVal("Whitespace", tokenname="WS")
TOKEN_VARSCOPE = EnumVal("Variable scope specifier", tokenname = "VARSCOPE")
TOKEN_VARQUANT = EnumVal("Variable quantity specifier", tokenname = "VARQUANT")
TOKEN_VARTYPE = EnumVal("Variable type specifier", tokenname = "VARTYPE")
TOKEN_IDENTIFIER = EnumVal("Identifier", tokenname = "IDENTIFIER")
TOKEN_ASSIGNMENTOP = EnumVal("Assignment operator", tokenname = "ASSIGNMENTOP", absorb_left = ABSORB_WS, absorb_right = ABSORB_WS)
TOKEN_BOOLOP_PREFIX = EnumVal("Boolean operator (prefix)", tokenname = "BOOLOP_PREFIX", absorb_right = ABSORB_WS_FORCED)
TOKEN_BOOLOP_INFIX = EnumVal("Boolean operator (infix)", tokenname = "BOOLOP_INFIX", absorb_left = ABSORB_WS_FORCED, absorb_right = ABSORB_WS_FORCED)
TOKEN_PREDICATE_SYMBOL = EnumVal("Infix predicate (symbol)", tokenname = "PREDICATE", absorb_left = ABSORB_WS, absorb_right = ABSORB_WS)
TOKEN_PREDICATE_KEYWORD = EnumVal("Infix predicate (keyword)", tokenname = "PREDICATE", absorb_left = ABSORB_WS_FORCED, absorb_right = ABSORB_WS_FORCED)

#TODO auto-generate this dict from an other list, to avoid code duplication
#(in other places, these strings are translated to constants such as VARSCOPE_GLOBAL)
KEYWORDS = {
	"global": TOKEN_VARSCOPE,
	"inherited": TOKEN_VARSCOPE,
	"local": TOKEN_VARSCOPE,
	"multi": TOKEN_VARQUANT,
	"single": TOKEN_VARQUANT,
	"string": TOKEN_VARTYPE,
	"path": TOKEN_VARTYPE,
	"int": TOKEN_VARTYPE,
	"not": TOKEN_BOOLOP_PREFIX,
	"and": TOKEN_BOOLOP_INFIX,
	"or": TOKEN_BOOLOP_INFIX,
	"xor": TOKEN_BOOLOP_INFIX,
	"implies": TOKEN_BOOLOP_INFIX,
	"subsetof": TOKEN_PREDICATE_KEYWORD
}

#TODO same thing here
SYMBOLS = {
	":=": TOKEN_ASSIGNMENTOP,
	"+=": TOKEN_ASSIGNMENTOP,
	"-=": TOKEN_ASSIGNMENTOP,
	"==": TOKEN_PREDICATE_SYMBOL
}

SPECIALCHARS = {
	"'": EnumVal("Single quote", tokenname = "'"),
	'"': EnumVal("Double quote", tokenname = '"'),
	"$": EnumVal("Dollar sign", tokenname = "$"),
	"[": EnumVal("Opening bracket", tokenname = "[", absorb_right = ABSORB_WS),
	"]": EnumVal("Closing bracket", tokenname = "]", absorb_left = ABSORB_WS),
	")": EnumVal("Opening parenthesis", tokenname = "(", absorb_right = ABSORB_WS),
	"(": EnumVal("Closing parenthesis", tokenname = ")", absorb_left = ABSORB_WS),
	"{": EnumVal("Opening brace", tokenname = "{", absorb_right = ABSORB_WS),
	"}": EnumVal("Closing brace", tokenname = "}", absorb_left = ABSORB_WS)
}

ESCAPABLECHARS = ''.join(SPECIALCHARS) + "\\ "

def tokenize_line(line):
	def tokenize_characters(line):
		"""
		tokenize (assign a type to) all characters of the input line
		resolve all \-escapes
		the returned type is a single char
		"""

		i = 0
		while i < len(line):
			c = line[i]
			if c == '\\':
				i += 1
				if i < len(line):
					c = line[i]
					if c in ESCAPABLECHARS:
						yield CHAR_OTHER, (c, i-1)
					elif c == 'x':
						try:
							val = int(line[i+1]+line[i+2], 16)
							yield CHAR_OTHER, (chr(val), i-1)
							i += 2
						except ValueError:
							raise TokenizerXEscapeIllegalCharacterException(i, "'\\x' escape", "two hex digits", line[i+1:i+3])
						except IndexError:
							raise TokenizerXEscapeEndOfLineException(i, "'\\x' escape", "two hex digits", "end of line")
					elif c == 'u':
						try:
							val = int(line[i+1]+line[i+2]+line[i+3]+line[i+4],16)
							yield CHAR_OTHER, (chr(val), i-1)
							i += 4
						except ValueError:
							raise TokenizerUEscapeIllegalCharacterException(i, "'\\u' escape", "four hex digits", line[i+1:i+5])
						except IndexError:
							raise TokenizerUEscapeEndOfLineException(i, "'\\u' escape", "four hex digits", "end of line")
					else:
						raise TokenizerEscapeIllegalCharacterException(i, "'\\' escape", "u, x, or one of '" + ESCAPE_ALLOWEDCHARS + "'", "'" + c + "'")
				else:
					raise TokenizerEscapeEndOfLineException(i, "'\\' escape", "u, x, or one of '" + ESCAPE_ALLOWEDCHARS + "'", "end of line")
			elif c in SPECIALCHARS:
				yield CHAR_SPECIAL, (c, i)
			elif c.isspace():
				yield CHAR_WS, (c, i)
			elif c in string.ascii_letters or c == '_':
				yield CHAR_ALPHABETIC, (c, i)
			elif c.isdigit():
				yield CHAR_DIGIT, (c, i)
			else:
				yield CHAR_OTHER, (c, i)
			i += 1

		yield CHAR_ENDOFSTATEMENT, (None, i)

	def condense_tokens(tokens):
		"""
		condense multiple chars of the same type to single tokens,
		to simplify the grammar, and make it LR(1)-parsable
		"""

		current_token_type = TOKEN_STARTOFSTATEMENT
		current_token_text = ""
		current_token_pos = -1

		for (chartype, (char, pos)) in tokens:
			if current_token_type == TOKEN_WS and chartype == CHAR_WS:
				#we've read an other whitespace, append
				current_text += char
			elif current_token_type == TOKEN_IDENTIFIER and chartype in [CHAR_ALPHABETIC, CHAR_DIGIT]:
				#we've read an other alphanumeric character
				current_text += char
			elif current_token_type == TOKEN_IDENTIFIER and chartype == CHAR_OTHER:
				#degrade token to 'literal', since it contains non-alphanum characters
				current_token_type = TOKEN_LITERAL
				current_text += char
			elif current_token_type == TOKEN_LITERAL and chartype in [CHAR_ALPHABETIC, CHAR_DIGIT, CHAR_OTHER]:
				#we've read an other literal character
				current_text += char
			else:
				#we've read a non-matching follow-on character
				#yield the current one, which is now finished.
				if current_token_type == TOKEN_LITERAL:
					if current_token_text in SYMBOLS:
						current_token_type = SYMBOLS[current_token_text]
				if current_token_type == TOKEN_IDENTIFIER:
					if current_token_text in KEYWORDS:
						current_token_type = KEYWORDS[current_token_text]
				yield current_token_type, (current_token_text, current_token_pos)

				#start a new token
				current_token_text = char
				current_token_pos = pos
				if chartype == CHAR_ALPHABETIC:
					current_token_type = TOKEN_IDENTIFIER
				elif chartype == CHAR_SPECIAL:
					current_token_type = SPECIALCHARS[char]
				elif chartype == CHAR_WS:
					current_token_type = TOKEN_WS
				elif chartype == CHAR_ENDOFSTATEMENT:
					yield TOKEN_ENDOFSTATEMENT, "", current_token_pos
				else:
					current_token_type = TOKEN_LITERAL

	#TODO take care of WS absorbtion here
	return [condense_tokens(tokenize_characters(line))]

class ConditionNode:
	def evaluate(self):
		raise NotImplementedError("evaluate not implemented in abstract base class")

class ConditionNotNode(ConditionNode):
	def __init__(self, child):
		self.child = child

	def __repr__(self):
		return "!(" + str(self.child) + ")"

	def evaluate(self):
		return not self.child.evaluate()

class ConditionJunctorNode(ConditionNode):
	def __init__(self, leftchild, rightchild):
		self.leftchild = leftchild
		self.rightchild = rightchild

class ConditionAndNode(ConditionJunctorNode):
	def __init__(self, leftchild, rightchild):
		ConditionJunctorNode.__init__(self, leftchild, rightchild)

	def __repr__(self):
		return "(" + str(self.leftchild) + ") & (" + str(self.rightchild) + ")"
	
	def evaluate(self):
		return self.leftchild.evaluate() and self.rightchild.evaluate()

class ConditionOrNode(ConditionJunctorNode):
	def __init__(self, leftchild, rightchild):
		ConditionJunctorNode.__init__(self, leftchild, rightchild)

	def __repr__(self):
		return "(" + str(self.leftchild) + ") | (" + str(self.rightchild) + ")"
	
	def evaluate(self):
		return self.leftchild.evaluate() or self.rightchild.evaluate()
	
def condition_test_equals(varval, val):
	return (varval == val)

def condition_test_matches(varval, val):
	return True # TODO stub

def condition_test_less(varval, val):
	return True # TODO stub

def condition_test_greater(varval, val):
	return True # TODO stub

class ConditionTestNode(ConditionNode):
	def __init__(self, vartoken, optoken, valtoken):
		self.var = vartoken.content
		self.val = evaluate_valstr(valtoken.content)
		op = optoken.content
		if op == "==" or op == "=":
			self.testfunc = condition_test_equals
			self.op = "=="
			self.invert = False
		elif op == "!=" or op == "<>":
			self.testfunc = condition_test_equals
			self.op = "!="
			self.invert = True
		elif op == "~=" or op == "=~":
			self.testfunc = condition_test_matches
			self.op = "~="
			self.invert = False
		elif op == "!~" or op == "~!":
			self.testfunc = condition_test_matches
			self.op = "!~"
			self.invert = True
		elif op == "<":
			self.testfunc = condition_test_less
			self.op = "<"
			self.invert = False
		elif op == ">":
			self.testfunc = condition_test_greater
			self.op = ">"
			self.invert = False
		elif op == "<=":
			self.testfunc = condition_test_greater
			self.op = "<="
			self.invert = True
		elif op == ">=":
			self.testfunc = condition_test_less
			self.op = ">="
			self.invert = True
		else:
			raise Exception("Unknown Operator: " + op + " at position " + str(optoken.pos));
	
	def __repr__(self):
		return self.var + self.op + str(self.val)

	def evaluate(self):
		varvalue = get_variable_value(self.var) # TODO get correct variable value
		result = testfunc(varvalue, self.val)
		if self.invert:
			return not result
		else:
			return result
