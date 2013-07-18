#!/usr/bin/python3
import collections

class EnumVal:
	"""
	simply functions as a named object, for use e.g. as enum value.
	"""
	def __init__(self, representation, **kw):
		self.representation = representation
		self.__dict__.update(kw)

	def __repr__(self):
		return self.representation

class OrderedDefaultDict(collections.OrderedDict):
	def __init__(self, *args, **kwargs):
		if not args:
			self.default_factory = None
		else:
			if not (args[0] is None or callable(args[0])):
				raise TypeError('first argument must be callable or None')
			self.default_factory = args[0]
			args = args[1:]
			super().__init__(*args, **kwargs)

	def __missing__ (self, key):
		if self.default_factory is None:
			raise KeyError(key)
		self[key] = default = self.default_factory()
		return default

class OrderedSet:
	"""
	we emulate 'OrderedSet' functionality from an OrderedDict by setting
	val = None.
	fak u python for not providing OrderedSet.
	"""
	def __init__(self):
		from collections import OrderedDict
		self.storage = OrderedDict()

	#append an element
	#returns true if the element was new
	def append(self, x):
		if x in self.storage:
			self.storage.pop(x)
			self.storage[x] = None
			return False
		else:
			self.storage[x] = None
			return True

	#delete an element
	def delete(self, x):
		self.storage.pop(x)

	#remove all elements
	def clear(self):
		self.storage.clear()

	#update the ordered set with an other ordered set
	def update(self, x):
		for v in x:
			if v in self.storage:
				self.storage.pop(v)
		self.storage.update(x.storage)

	def tolist(self):
		return [x for x in self.storage]

	def newest(self):
		return next(reversed(self.storage))

	def __iter__(self):
		return self.storage.__iter__()
