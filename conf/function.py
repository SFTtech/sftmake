from util.misc import inf

functions = {}

class Function:
	def __init__(self, name, valtype, code, minargc = 0, maxargc = inf):
		self.name = name
		self.valtype = valtype
		self.code = code
		self.minargc = minargc
		self.maxargc = maxargc
		functions[name] = self

	def call(vallist):
		if len(vallist) < self.minargc:
			raise 
		return self.code(vallist)
