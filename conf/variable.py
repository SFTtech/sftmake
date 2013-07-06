from conf import variables
from conf import assignment
from conf.exceptions import *
from util import OrderedDefaultDict

""" Assignment values are treated as strings, without any semantics """
VALTYPE_STRING = EnumVal("Value type: String")
""" Assignment values are treated as paths, relative to the directory of the config file """
VALTYPE_PATH = EnumVal("Value type: Path")
""" Assignment values are treated as integers """
VALTYPE_INT = EnumVal("Value type: Int")
valtypes = {
	"string": TYPE_STRING,
	"path":   TYPE_PATH,
	"int":    TYPE_INT
}

""" Only the last value that has been assigned to the variable counts """
VALCOUNT_SINGLE = EnumVal("Value count: Single value")
""" All values that have been assigned count """
VALCOUNT_LIST = EnumVal("Value count: List")
valcounts = {
	"single": QUANT_SINGLE,
	"multi":  QUANT_MULTI
}

""" Only the variable assignments from this config count """
ASSIGNMENTSCOPE_LOCAL = EnumVal("Assignment scope: Local")
""" The variable assignments from this config and all parent configs count """
ASSIGNMENTSCOPE_INHERITED = EnumVal("Assignment scope: Inherited")
""" All variable assignments from all configs count """
ASSIGNMENTSCOPE_GLOBAL = EnumVal("Assignment scope: Global")
assignmentscopes = {
	"local":     SCOPE_LOCAL,
	"inherited": SCOPE_MULTI,
	"global":    SCOPE_GLOBAL
}

class Var:
	"""
	One complete configuration variable, such as 'cflags'.
	Its value [list] for a certain conf is defined by its list of assignments
	"""
	def __init__(self, name,
		assignmentscope = ASSIGNMENTSCOPE_INHERITED,
		valtype = VALTYPE_STRING,
		valcount = VALCOUNT_LIST):
		"""
		The newly created variable is automatically entered into the config.variables array
		"""
		self.name = name
		self.assignmentscope = assignmentscope
		self.valtype = valtype
		self.valcount = valcount
		self.assignments = OrderedDefaultDict(lambda: [])

		variables[name] = self

	def assign(self, conf, assignment):
		"""
		assigns the assignment to this variable, scoped for conf
		note that even for variables with ASSIGNMENTSCOPE_GLOBAL,
		conf has a relevancebecause it determines the order of the assignments
		"""
		self.assignments[conf] = assignment

	def eval(self, conf, depends = OrderedSet()):
		"""
		determines the value [list] of the var, for a certain conf

		conf:
			the conf for which we wish to evaluate the variable
			note that evalconf is relevant even for variables with global assignment scopes,
			as other, non-global variables may be relevant for evaluation.
		depends:
			as already noted above, the evaluation of a variable might involve the
			evaluation of other variables.
			the result is a directed evaluation graph, where node may have an arbitrary number
			of following variables.
			if that graph is not a tree (not loop-free), the evaluation process will not terminate;
			we need to detect such situations.
			'depends' contains a list of all tree nodes (variables) that have been visited in the
			current path of evaluation; duplicate entries mean detection of a loop
		"""
		if depends.append(self) == False:
			raise CircularDependencyException(depends, self.name)

		if self.varscope == ASSIGNMENTSCOPE_INHERITED:
			#the confs of all parents are relevant (order from parent to child)
			relevantconfs = conf.parenthyperres()
		elif self.varscope == ASSIGNMENTSCOPE_LOCAL:
			#only this conf is relevant
			relevantconfs = [conf]
		elif self.varscope == ASSIGNMENTSCOPE_GLOBAL:
			#all confs are relevant (order equals the order in which the conffiles were read)
			relevantconfs = self.assignments

		result = OrderedSet()
		for assignmentconf in relevantconfs:
			for a in self.assignments[assignmentconf]:
				if not a.condition.eval(conf, depends):
					continue

				vallist = a.expressionlist.eval(conf, depends, self.valtype)

				#apply vallist to result, in the way specified by a.mode
				if a.mode == assignment.MODE_APPEND:
					for v in vals:
						result.append(s)
				elif a.mode == assignment.MODE_SET:
					result.clear()
					for v in vals:
						result.append(s)
				elif a.mode == assignment.MODE_REMOVE:
					for v in vals:
						result.remove(s)

		if self.valcount == VALCOUNT_SINGLE:
			try:
				return result.newest()
			except:
				raise Exception("Single-quantified variable has no value")
		elif self.varquant == VALCOUNT_MULTI:
			return result

	def __repr__(self):
		result = "Name: " + self.name + "\n"
		result += str(self.assignmentscope) + "\n"
		result += str(self.valtype) + "\n"
		result += str(self.valcount) + "\n"
		result += "Assignments:" + "\n"
		for conf in self.assignments:
			result += repr(conf) + ":\n"
			for ass in self.assignments[conf]:
				result += "\t" + self.name + repr(ass) + "\n"
		return result[:-1]
