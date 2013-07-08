from util.datatypes import EnumVal

""" The values from the assignment are appended to the result list of the variable """
MODE_APPEND = EnumVal("Assignment mode: Append")
""" The values from the assignment replace the result list of the variable """
MODE_SET    = EnumVal("Assignment mode: Set")
""" The values from the assignment are removed from the result list of the variable """
MODE_REMOVE = EnumVal("Assignment mode: Remove")

assignmentops = {
	"+=": MODE_APPEND,
	":=": MODE_SET,
	"-=": MODE_REMOVE
}

class Assignment:
	"""
	represents one assignment of an expression list to a variable

	expressionlist
		An ExpressionList object, which is evaluated on variable evaluation.
	condition
		A BooleanExpression object, which must evaluate to True during variable evaluation for
		the assignment to have any effect.
	mode
		The way the assignment effects the resulting value list of a variable on evaluation
	src
		A human-readable string that describes the source of this assignment,
		for use in dbg/error messages; e.g. '^/smfile:80' or 'argv[3]'
	"""

	def __init__(self, expressionlist, condition, mode, src):
		self.expressionlist = expressionlist
		self.condition = condition
		self.mode = mode
		self.src = src

	def op(self):
		for op in assignmentops:
			if assignmentops[op] == self.mode:
				return op
		return None

	def __repr__(self):
		return '[' + repr(self.condition) + ']' + self.op() + " ".join(self.expressionlist) + " #" + self.src
