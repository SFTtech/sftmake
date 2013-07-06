class CondTreeNode:
	"""
	represents one condition tree node.
	assignment conditions consist of a list of condition tree nodes, which may in return have more
	condition tree nodes as children.
	consider the example: cflags[$mode==dbg] += -g
		the condition is one CondTreeNode which checks whether $mode equals dbg.
	consider the example: cflags[$mode==dbg || $mode==dbgo] += -g
		the condition is one CondTreeNode of type 'or', which has two children.
		one child checks whether $mode equals dbg, and the other one checks wheter $mode equals dbgo
	"""

	def eval(self, evalconf, depends):
		"""
		evaluates whether the condition is met.

		evalconf
			the conf for which we are evaluating
		depends
			for detecting circular variable dependencies (and thus infinite loops)
		"""
		#not implemented in abstract base class
		raise NotImplementedError()

class CondTreeNode_Not(CondTreeNode):
	"""
	logic 'not' of one condition
	"""
	def __init__(self, condtree):
		self.condtree = condtree

	def __repr__(self):
		return "not(" + repr(self.condtree) + ")"

	def eval(self, evalconf, depends):
		return not self.condtree.eval(evalconf, depends)

class CondTreeNode_And(CondTreeNode):
	"""
	logic 'and' of multiple conditions
	evaluation stops when the first false condition is encountered
	"""
	def __init__(self, condtrees):
		self.condtrees = condtrees

	def __repr__(self):
		return "and(" + repr(self.condtrees) + ")"

	def eval(self, evalconf, depends):
		for c in self.condtrees:
			if not c.eval(evalconf, depends):
				return False

		return True

class CondTreeNode_Or(CondTreeNode):
	"""
	logic 'or' of multiple conditions
	evaluation stops when the first true condition is encountered
	"""
	def __init__(self, condtrees):
		self.condtrees = condtrees

	def __repr__(self):
		return "or(" + repr(self.condtrees) + ")"

	def eval(self, evalconf, depends):
		for c in self.condtrees:
			if c.eval(evalconf, depends):
				return True

		return False

class CondTreeNode_Xor(CondTreeNode):
	"""
	logic 'xor' of multiple conditions
	true if an odd number of conditions evaluate to true
	all conditions are evaluated
	"""
	def __init__(self, condtrees):
		self.condtrees = condtrees

	def __repr__(self):
		return "xor(" + repr(self.condtrees) + ")"

	def eval(self, evalconf, depends):
		result = False

		for c in self.condtrees:
			if c.eval(evalconf, depends):
				result = not result

		return result

class CondTreeNode_Implies(CondTreeNode):
	"""
	logic 'implies' of two conditions
	true if the left condition is false, or if left and right are true
	the right condition is not evaluated if the left condition is false
	"""
	def __init__(self, condtreel, condtreer):
		self.condtreel = condtreel
		self.condtreer = condtreer

	def __repr__(self):
		return "(" + repr(self.condtreel) + ") -> (" + repr(self.condtreer) + ")"

	def eval(self, evalconf, depends):
		return not condtreel.eval(evalconf, depends) or condtreer.eval(evalconf, depends)

class CondTreeNode_Leaf(CondTreeNode):
	"""
	abstract class that represents a condtree leaf node,
	i.e. one that actually checks a condition,
	such as 'equals', 'greater than', 'subset', ...
	"""
	def __init__(self, leftvals, rightvals):
		"""
		leftvals
			ValTreeNode for the vals left of the operator
		rightvals
			ValTreeNode for the vals right vor the operator
		"""
		self.leftvals = leftvals
		self.rightvals = rightvals

	def __repr__(self):
		return "(" + repr(self.leftvals) + " " + self.operator + " " + repr(self.rightvals) + ")"

	def evallr(self, evalconf, depends):
		"""
		evaluate the left and right valtrees
		used by the eval() methods
		"""
		left = self.leftvals.eval(evalconf, Var.TYPE_STRING, depends)
		right = self.rightvals.eval(evalconf, Var.TYPE_STRING, depends)
		return left, right

	def select(operator):
		"""
		selects the appropriate CondTreeNode leaf type, from the given operator
		"""
		if operator in ["==", "=", "equals", "eq"]:
			return CondTreeNode_Leaf_Equals
		elif operator in ["subset of", "subsumes"]:
			return CondTreeNode_Leaf_SubSet
		else:
			raise Exception("Unknown condition operator")

class CondTreeNode_Leaf_Equals(CondTreeNode_Leaf):
	"""
	checks whether the left and right expressions are equal
	note that in the current implementation, this also checks whether the order is identical.
	maybe introduce a '===' operator for that? TODO
	"""
	operator = "=="

	def check(self, evalconf, depends):
		leftvals, rightvals = self.evallr(evalconf, depends)
		return leftvals == rightvals

class CondTreeNode_Leaf_SubSet(CondTreeNode_Leaf):
	"""
	checks whether the left expression is a subset of the right expression
	does not take order into consideration
	"""
	operator = "subset of"

	def check(self, evalconf, depends):
		leftvals, rightvals = self.evallr()
		return set(leftvals) < set(rightvals)
