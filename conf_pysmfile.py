#!/usr/bin/python3

# this file is, again, part of [sft]make
#
# licensed GPLv3 or later, no warranty, gschichten.
#
# as the sftmake config language and it's parsing is struggling
# in it's development, this is an attempt to configure sftmake
# via the regular python language
#
# (c) 2013 [sft]technologies


'''
class for working with a smfile
containing configuration written in python
'''
class pysmfile:

	def __init__(self, filepath):
		self.filepath = filepath
		with open(self.filepath) as f:
			self.content = f.read()


	def dump_content(self):
		print(str(self.content))
