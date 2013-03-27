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

def tokenize_line(line):
	#TODO use the new Enum stuff from util
	
	def tokenize_characters(line):
		"""
		tokenize (assign a type to) all characters of the input line
		resolve all \-escapes
		the returned type is a single char
		"""
		SPECIALCHARS = "!=<>()[]{}$'\"|&,;:~+-"
		ESCAPE_ALLOWEDCHARS = SPECIALCHARS + "\\ "

		i = 0
		while i < len(line):
			c = line[i]
			if c == '\\':
				i += 1
				if i < len(line):
					c = line[i]
					if c in ESCAPE_ALLOWEDCHARS:
						yield ('o', (c, i-1))
					elif c == 'x':
						try:
							val = int(line[i+1]+line[i+2], 16)
							yield ('o', (chr(val), i-1))
							i += 2
						except ValueError:
							raise TokenizerXEscapeIllegalCharacterException(i, "'\\x' escape", "two hex digits", line[i+1:i+3])
						except IndexError:
							raise TokenizerXEscapeEndOfLineException(i, "'\\x' escape", "two hex digits", "end of line")
					elif c == 'u':
						try:
							val = int(line[i+1]+line[i+2]+line[i+3]+line[i+4],16)
							yield ('o', (chr(val), i-1))
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
				yield (c, (c, i))
			elif c.isspace(): 
				yield ('w', (c, i)) #w == WHITESPACE
			elif c in string.ascii_letters or c == '_':
				yield ('a', (c, i)) #a == ALPHA
			elif c.isdigit():
				yield ('d', (c, i)) #d == DIGIT
			else:
				yield ('o', (c, i)) #o == OTHER
			i += 1
	
	def condense_tokens(tokens):
		"""
		condense multiple chars of the same type to single tokens,
		to simplify the grammar, and make it LR(1)-parsable
		"""

		current_name = ""
		current_text = ""
		current_pos = -1

		for (name, (char, pos)) in tokens:
			if current_name == "WHITESPACE" and name == "w":
				#we've read an other whitespace, append
				current_text += char
			elif current_name == "IDENTIFIER" and name in "ad":
				#we've read an other alphanumeric character
				current_text += char
			elif current_name == "IDENTIFIER" and name == "o":
				#degrade token to 'literal', since it contains non-alphanum characters
				current_name = "LITERAL"
				current_text += char
			elif current_name == "LITERAL" and name in "ado":
				#we've read an other literal character
				current_text += char
			else:
				#we've read a non-matching follow-on token. write away the current token

				#if we're at the (empty) start token, don't write it to the list
				if current_name != "":
					yield current_name, current_text, current_pos

				#initialize new current token
				current_name = str(name)
				current_text = str(char)
				current_pos = pos

				#literal characters get a special treatment
				if current_name == "a":
					current_name = "IDENTIFIER"
				elif current_name == "w":
					current_name = "WHITESPACE"
				elif current_name in "do":
					current_name = "LITERAL"
		
		if current_name != "":
			yield current_name, current_text, current_pos

	tokens = []
	for name, text, pos in condense_tokens(tokenize_characters(line)):
		if name == "IDENTIFIER" and text in ["single", "multi"]:
			name = "VARQUANT"
		if name == "IDENTIFIER" and text in ["string", "path", "int"]:
			name = "VARTYPE"
		tokens.append((name, (text, pos)))

	return tokens

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
