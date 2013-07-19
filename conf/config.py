from util.datatypes import EnumVal, OrderedSet

from conf import configs

class Config:
	"""
	other than the name might suggest, this class holds no actual config data.
	it merely manages metadata for configurations such as their name, and their parent configurations.
	actual config data is stored by the Var objects

	name
		example conf names:

		default
		args
		^
		^/libsft
		^/main.cpp
		^/libsft:^/main.cpp

	conftype
		One of
			TYPE_BASE (the 'default' and 'args' configs),
			TYPE_DIR,
			TYPE_TARGET,
			TYPE_SRC,
			TYPE_SRCFORTARGET

	parents
		list of pointers to direct parent configurations

		example parent lists:

		base:default
			[]
		dir:^
			[base:args]
		srcfortarget:^/libsft:^/main.cpp
			[target:^/libsft, src:^/main.cpp]

	directory
		the directory relative to which relative paths sould be interpreted

		example directories:

		base:default
			^
		dir:^
			^
		dir:^/tests
			^/tests
		src:^/tests/main.cpp
			^/tests
		srcfortarget:^/tester:^/tests/main.cpp
			^/tests
	"""

	TYPE_BASE = EnumVal("Base config")
	TYPE_DIR = EnumVal("Directory config")
	TYPE_TARGET = EnumVal("Target config")
	TYPE_SRC = EnumVal("Sourcefile config")
	TYPE_SRCFORTARGET = EnumVal("Source-for-target config")

	def __init__(self, name, conftype, parents, directory):
		self.name = name
		self.conftype = conftype
		self.parents = parents
		self.directory = directory
		configs[name] = self

	def __repr__(self):
		result = repr(self.conftype) + ": " + self.name + " (dir: " + self.directory
		result += "; parents: " + repr([paren.name for paren in self.parents]) + ")"
		return result

	def parenthyperres(self):
		"""
		Returns whole inheritance list for the conf,
		starting with the most base conf 'default', and ending with self.
		"""
		result = OrderedSet()
		for parent in self.parents:
			result.update(parent.parenthyperres())
		result.append(self)
		return result
