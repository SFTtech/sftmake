import string
from util.misc import inf
from util.datatypes import EnumVal
from parser.exceptions import *

class TokenType:
	def __init__(self, name, absorb_left = False, absorb_right = False, condensable = False):
		self.name = name
		self.absorb_left = absorb_left
		self.absorb_right = absorb_right
		self.condensable = condensable

	def __repr__(self):
		return self.name

class Token:
	def __init__(self, tokentype, text, pos):
		self.tokentype = tokentype
		self.text = text
		self.pos = pos

	def __repr__(self):
		return str(self.tokentype) + ": '" + str(self.text) + "'"

	def totuple(self):
		return self.tokentype.name, (self.text, self.pos)

#constants for tokenizer
TOKEN_STARTOFSTATEMENT = TokenType("STARTOFSTATEMENT", absorb_right = True)
TOKEN_ENDOFSTATEMENT = TokenType("ENDOFSTATEMENT", absorb_left = True)

TOKEN_WS = TokenType("WS", condensable = True)
TOKEN_LITERAL = TokenType("LITERAL", condensable = True)

TOKEN_VARSCOPE = TokenType("VARSCOPE")
TOKEN_VARQUANT = TokenType("VARQUANT")
TOKEN_VARTYPE = TokenType("VARTYPE")
TOKEN_IDENTIFIER = TokenType("IDENTIFIER")
TOKEN_ASSIGNMENTOP = TokenType("ASSIGNMENTOP", absorb_left = True, absorb_right = True)
TOKEN_BOOLOP_PREFIX = TokenType("BOOLOP_PREFIX", absorb_right = True)
TOKEN_BOOLOP_INFIX = TokenType("BOOLOP_INFIX", absorb_left = True, absorb_right = True)
TOKEN_PREDICATE_SYMBOL = TokenType("PREDICATE", absorb_left = True, absorb_right = True)
TOKEN_PREDICATE_KEYWORD = TokenType("PREDICATE", absorb_left = True, absorb_right = True)

#TODO auto-generate this dict from an other list, to avoid code duplication
#(in other places, these strings are translated to constants such as VARSCOPE_GLOBAL)
TOKEN_KEYWORDS = {
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
	"subsetof": TOKEN_PREDICATE_KEYWORD,
	"in": TOKEN_PREDICATE_KEYWORD
}

#TODO same thing here
TOKEN_SYMBOLS = {
	":=": TOKEN_ASSIGNMENTOP,
	"+=": TOKEN_ASSIGNMENTOP,
	"-=": TOKEN_ASSIGNMENTOP,
	"==": TOKEN_PREDICATE_SYMBOL,
	"<":  TOKEN_PREDICATE_SYMBOL
}

TOKEN_SPECIALCHARS = {
	"'": TokenType("'"),
	'"': TokenType('"'),
	'$': TokenType('$'),
	'[': TokenType('[', absorb_right = True),
	']': TokenType(']', absorb_left = True),
	'(': TokenType('(', absorb_right = True),
	')': TokenType(')', absorb_left = True),
	'{': TokenType('{', absorb_right = True),
	'}': TokenType('}', absorb_left = True)
}

ESCAPABLECHARS = ''.join(TOKEN_SPECIALCHARS) + "\\ "

def tokenize_chars(chars):
	"""
	tokenize the statement character-by character, resolving \-escapes
	"""
	yield Token(TOKEN_STARTOFSTATEMENT, "", -1)
	i = 0
	while i < len(chars):
		c = chars[i]
		if c == '\\':
			i += 1
			if i < len(chars):
				c = chars[i]
				if c in ESCAPABLECHARS:
					yield Token(TOKEN_LITERAL, c, i-1)
				elif c == 'x':
					try:
						val = int(chars[i+1]+chars[i+2], 16)
						yield Token(TOKEN_LITERAL, val, i-1)
						i += 2
					except ValueError:
						raise TokenizerXEscapeIllegalCharacterException(i, "'\\x' escape", "two hex digits", chars[i+1:i+3])
					except IndexError:
						raise TokenizerXEscapeEndOfLineException(i, "'\\x' escape", "two hex digits", "end of statement")
				elif c == 'u':
					try:
						val = int(chars[i+1]+chars[i+2]+chars[i+3]+chars[i+4],16)
						yield Token(TOKEN_LITERAL, chr(val), i-1)
						i += 4
					except ValueError:
						raise TokenizerUEscapeIllegalCharacterException(i, "'\\u' escape", "four hex digits", chars[i+1:i+5])
					except IndexError:
						raise TokenizerUEscapeEndOfLineException(i, "'\\u' escape", "four hex digits", "end of statement")
				else:
					raise TokenizerEscapeIllegalCharacterException(i, "'\\' escape", "u, x, or one of '" + ESCAPE_ALLOWEDCHARS + "'", "'" + c + "'")
			else:
				raise TokenizerEscapeEndOfLineException(i, "'\\' escape", "u, x, or one of '" + ESCAPE_ALLOWEDCHARS + "'", "end of statement")
		elif c in TOKEN_SPECIALCHARS:
			yield Token(TOKEN_SPECIALCHARS[c], c, i)
		elif c.isspace():
			yield Token(TOKEN_WS, c, i)
		else:
			yield Token(TOKEN_LITERAL, c, i)
		i += 1

	yield Token(TOKEN_ENDOFSTATEMENT, "", i)

def condense_tokens(tokens):
	"""
	condense multiple tokens of the same type to larger tokens,
	to make the grammar LR(1)-parsable
	"""
	current = None
	for token in tokens:
		if current != None and current.tokentype.condensable and current.tokentype == token.tokentype:
			current.text += token.text
		else:
			if current != None:
				yield current
			current = token

	if current != None:
		yield current

def replace_symbols(tokens):
	for token in tokens:
		if token.tokentype == TOKEN_LITERAL:
			#check whether the token text contains any symbols,
			#and split it at them
			while True:
				best_occurence = inf, 0, None
				for symbol in TOKEN_SYMBOLS:
					pos = token.text.find(symbol)
					if pos < 0:
						continue
					best_occurence = min(best_occurence, (pos, -len(symbol), symbol))
				if best_occurence[0] == inf:
					break

				#of all leftmost occurences, we have found that of the longest symbol
				#time to split the token in thrice
				occpos, occlen, symbol = best_occurence
				occlen = -occlen
				if symbol == None:
					break

				if occpos > 0:
					yield(Token(TOKEN_LITERAL, token.text[:occpos], token.pos))
				if occlen + occpos < len(token.text):
					yield Token(TOKEN_SYMBOLS[symbol], symbol, token.pos + occpos)
					token.pos += occpos + occlen
					token.text = token.text[occpos + occlen:]
				else:
					token.tokentype = TOKEN_SYMBOLS[symbol]
					token.text = symbol
					token.pos += occpos
					break
		yield token

def replace_keywords_and_identifiers(tokens):
	for token in tokens:
		if token.tokentype == TOKEN_LITERAL:
			if token.text in TOKEN_KEYWORDS:
				token.tokentype = TOKEN_KEYWORDS[token.text]
			elif token.text.isidentifier():
				token.tokentype = TOKEN_IDENTIFIER
		yield token

def absorb_whitespaces(tokens):
	"""
	as a further optimization to simplify the grammar's handling of whitespaces, many token types
	absorb neighboring whitespace tokens, nullifying them.
	"""
	tokens = list(tokens)
	for i in range(1, len(tokens) - 1):
		if tokens[i].tokentype == TOKEN_WS:
			if tokens[i - 1].tokentype.absorb_right:
				tokens[i - 1].text = tokens[i - 1].text + tokens[i].text
				tokens[i] = None
				continue
			if tokens[i + 1].tokentype.absorb_left:
				tokens[i + 1].text = tokens[i].text + tokens[i + 1].text
				tokens[i] = None
				continue
	return (token for token in tokens if token != None)

def tokenize_statement(statement):
	tokens = tokenize_chars(statement)
	tokens = condense_tokens(tokens)
	tokens = replace_symbols(tokens)
	tokens = replace_keywords_and_identifiers(tokens)
	tokens = absorb_whitespaces(tokens)
	return tokens
