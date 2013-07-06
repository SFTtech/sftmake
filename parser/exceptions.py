class ParserException(Exception):
	def __init__(self, pos, situation, expected, got):
		Exception.__init__(self, situation + ", expected " + expected + ", but got " + got)
		self.pos = pos
		self.situation = situation
		self.expected = expected
		self.got = got

class ParserUnexpectedTokenException(Exception):
	def __init__(self, token, expected_tokens):
		self.token = token
		self.expected_tokens = expected_tokens

		got = repr(token[1][0]) + " (" + repr(token[0]) + ")"

		expected = [repr(t) for t in expected_tokens]
		if len(expected) == 0:
			expected = "nothing"
		elif len(expected) == 1:
			expected = expected[0]
		else:
			expected = expected[0] + " or " + ", ".join(expected[1:])
		ParserException.__init__(self, token[1][1], "At position "+ str(token[1][1]), expected, got)

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
