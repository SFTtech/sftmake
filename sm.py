#!/usr/bin/python3

# this file is, again, part of [sft]make
#
# include it in your python-configurated smfiles
#
# licensed GPLv3 or later, no warranty, gschichten.
#
# as the sftmake config language and it's parsing is struggling
# in it's development, this is an attempt to configure sftmake
# via the regular python language
#
# (c) 2013 [sft]technologies, jonas jelten

import pprint
from util.datatypes import EnumVal

class smconfig:

	def __init__(self):
		self.data = dict()

	def lol(self):
		print("smconfig call test successful")

	def set(self, key, val):
		self.data[key] = val

	def add(self, key, val):
		if key in self.data:
			if type(self.data[key]) == list:
				self.data[key].append(val)
			else:
				raise Exception("can't append value '" + val + "' to key [" + str(key) + "] as it is not a list.")

		else:
			self.data[key] = [val]

	def remove(self, key):
		del self.data[key]

	def get(self, key):
		return self.data[key]

	def __repr__(self):
		return "[smconfig]"

	def __str__(self):
		return pprint.pformat(self.data)


#if everything should be built, 'build' has to be:
everything = EnumVal("everything")



# c[$srcsuffix == c] = gcc in confnodes:
#VarAssignment(
#	valtree = ValTreeNode_StringLiteral(conf_default, "gcc"),
#	condtree = CondTreeNode_Leaf_Equals(
#		ValTreeNode_Var(conf_default, ValTreeNode_StringLiteral(conf_default, "srcsuffix")),
#		ValTreeNode_StringLiteral(conf_default, "c")
#	),
#	mode = VarAssignment.MODE_APPEND,
#	src = "default configuration"
#)

#TODO: classes for all output types (e.g. binary, sharedlib, staticlib, ...)
# options like gcc -Wl,-rpath=.,-shared,-static etc
